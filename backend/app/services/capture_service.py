import hashlib
import logging
import queue
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg2
from fastapi import HTTPException, status
from psycopg2.extras import execute_values, RealDictCursor

from ..config import settings
from .detection_service import evaluate_packets

logger = logging.getLogger("netshield.capture")


class CaptureManager:
    def __init__(self, max_queue_size: int = 5000, batch_size: int = 100):
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self._lock = threading.RLock()
        self._session: dict[str, Any] | None = None

    def discover_interfaces(self) -> list[dict[str, Any]]:
        try:
            from scapy.all import conf
            from scapy.arch.windows import get_windows_if_list
        except ImportError:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Packet capture dependency is not installed.",
            )

        try:
            windows_interfaces = get_windows_if_list()
            interfaces = []
            for index, interface in enumerate(windows_interfaces):
                capture_name = interface.get("name")
                interface_id = capture_name or interface.get("guid") or str(index)
                name = interface.get("description") or interface.get("name") or interface_id
                interfaces.append({
                    "id": interface_id,
                    "name": name,
                    "description": interface.get("description"),
                    "mac": interface.get("mac"),
                    "win_index": interface.get("win_index"),
                    "guid": interface.get("guid"),
                    "available": True,
                })
            if interfaces:
                return interfaces

            for interface in conf.ifaces.values():
                interfaces.append({
                    "id": getattr(interface, "network_name", None)
                    or getattr(interface, "guid", None)
                    or str(interface),
                    "name": getattr(interface, "description", None)
                    or getattr(interface, "name", None)
                    or str(interface),
                    "description": getattr(interface, "description", None),
                    "mac": getattr(interface, "mac", None),
                    "win_index": None,
                    "available": True,
                })
            return interfaces
        except Exception as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"Unable to enumerate Npcap interfaces: {exc}",
            )

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            if self._session is None:
                return {
                    "active": False,
                    "session": None,
                    "live_capture_enabled": True,
                }
            session = self._session
            return {
                "active": session["running"].is_set(),
                "session": {
                    "id": session["id"],
                    "interface_id": session["interface_id"],
                    "interface_name": session["interface_name"],
                    "started_at": session["started_at"].isoformat(),
                    "packets_received": session["packets_received"],
                    "packets_inserted": session["packets_inserted"],
                    "packets_dropped": session["packets_dropped"],
                    "error": session["error"],
                },
                "live_capture_enabled": True,
            }

    def start(self, conn, user, interface_id: str) -> dict[str, Any]:
        with self._lock:
            if self._session is not None and self._session["running"].is_set():
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "A live capture session is already running.",
                )

            interface = next(
                (
                    item
                    for item in self.discover_interfaces()
                    if item["id"] == interface_id
                ),
                None,
            )
            if interface is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "The selected network interface is unavailable.",
                )

            session_id = str(uuid.uuid4())
            started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            packet_queue = queue.Queue(maxsize=self.max_queue_size)
            running = threading.Event()
            running.set()

            session = {
                "id": session_id,
                "interface_id": interface_id,
                "interface_name": interface["name"],
                "started_at": started_at,
                "running": running,
                "queue": packet_queue,
                "packets_received": 0,
                "packets_inserted": 0,
                "packets_dropped": 0,
                "error": None,
                "sniffer": None,
                "worker": None,
                "started_callback": threading.Event(),
            }
            self._session = session

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO network_capture_sessions
                        (id, interface_id, interface_name, started_by_user_id,
                         status, started_at)
                    VALUES (%s, %s, %s, %s, 'running', %s)
                    """,
                    (
                        session_id,
                        interface_id,
                        interface["name"],
                        user.id,
                        started_at,
                    ),
                )
                conn.commit()

            worker = threading.Thread(
                target=self._database_writer,
                args=(session,),
                name=f"netshield-capture-db-{session_id[:8]}",
                daemon=True,
            )
            session["worker"] = worker
            worker.start()

            try:
                from scapy.all import AsyncSniffer

                session["sniffer"] = AsyncSniffer(
                    iface=interface_id,
                    prn=lambda packet: self._enqueue(session, packet),
                    store=False,
                    started_callback=session["started_callback"].set,
                )
                session["sniffer"].start()
                if not session["started_callback"].wait(timeout=5):
                    raise RuntimeError("Capture receive loop did not start within 5 seconds")
            except Exception as exc:
                session["error"] = str(exc)
                session["running"].clear()
                self._persist_stop(session, "failed", str(exc))
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    f"Unable to start capture: {exc}",
                )

            return self.get_status()["session"]

    def _enqueue(self, session: dict[str, Any], packet: Any) -> None:
        try:
            metadata = self._packet_metadata(session, packet)
            session["queue"].put(metadata, block=False)
            session["packets_received"] += 1
        except queue.Full:
            session["packets_dropped"] += 1
        except Exception as exc:
            session["error"] = str(exc)
            logger.exception("Packet metadata or queue insertion failed")

    def _packet_metadata(
        self, session: dict[str, Any], packet: Any
    ) -> tuple[Any, ...]:
        from scapy.layers.inet import IP, TCP, UDP, ICMP
        from scapy.layers.inet6 import IPv6

        timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        source_ip = None
        destination_ip = None
        source_port = None
        destination_port = None
        protocol = "Other"

        if packet.haslayer(IP):
            source_ip = packet[IP].src
            destination_ip = packet[IP].dst
            protocol = "TCP" if packet.haslayer(TCP) else (
                "UDP" if packet.haslayer(UDP) else (
                    "ICMP" if packet.haslayer(ICMP) else "IP"
                )
            )
        elif packet.haslayer(IPv6):
            source_ip = packet[IPv6].src
            destination_ip = packet[IPv6].dst
            protocol = "TCP" if packet.haslayer(TCP) else (
                "UDP" if packet.haslayer(UDP) else "IPv6"
            )

        if packet.haslayer(TCP):
            source_port = int(packet[TCP].sport)
            destination_port = int(packet[TCP].dport)
        elif packet.haslayer(UDP):
            source_port = int(packet[UDP].sport)
            destination_port = int(packet[UDP].dport)

        try:
            packet_size = len(packet)
        except Exception:
            packet_size = None

        frame_number = session["packets_received"] + 1
        import_key = hashlib.md5(
            (
                f"{session['id']}|{frame_number}|{timestamp.isoformat()}|"
                f"{source_ip or ''}|{destination_ip or ''}|"
                f"{source_port or ''}|{destination_port or ''}|"
                f"{protocol}|{packet_size or ''}"
            ).encode("utf-8")
        ).hexdigest()

        return (
            timestamp,
            source_ip,
            destination_ip,
            source_port,
            destination_port,
            protocol,
            packet_size,
            session["id"],
            frame_number,
            True,
            "confirmed",
            "unknown",
            "live_capture",
            import_key,
        )

    def _database_writer(self, session: dict[str, Any]) -> None:
        while session["running"].is_set() or not session["queue"].empty():
            batch = []
            try:
                batch.append(session["queue"].get(timeout=0.1))
                while len(batch) < self.batch_size:
                    batch.append(session["queue"].get_nowait())
            except queue.Empty:
                pass
            except Exception as exc:
                session["error"] = str(exc)
                logger.exception("Capture queue read failed")

            if batch:
                self._insert_batch(session, batch)

    def _insert_batch(
        self, session: dict[str, Any], batch: list[tuple[Any, ...]]
    ) -> None:
        connection = None
        try:
            connection = psycopg2.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                dbname=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
            )
            with connection:
                with connection.cursor() as cursor:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO public.network_packets (
                            packet_timestamp, source_ip, destination_ip,
                            source_port, destination_port, protocol, packet_size,
                            capture_id, frame_number, protocol_confirmed,
                            protocol_confidence, traffic_direction,
                            capture_source, import_key
                        ) VALUES %s
                        ON CONFLICT (import_key) DO NOTHING
                        """,
                        batch,
                        page_size=self.batch_size,
                    )
                    session["packets_inserted"] += cursor.rowcount
                    if session["packets_inserted"] > 0:
                        evaluate_packets(
                            connection,
                            capture_source="live_capture",
                            capture_id=session["id"],
                        )
        except Exception as exc:
            session["error"] = str(exc)
            logger.error("Packet database batch insertion failed: %s", exc)
        finally:
            if connection is not None:
                connection.close()

    def _stop_sniffer(self, sniffer: Any) -> None:
        try:
            try:
                sniffer.stop(join=True)
                return
            except Exception:
                pass
            sniffer.running = False
            socket = getattr(sniffer, "socket", None)
            if socket is not None:
                try:
                    socket.close()
                except Exception:
                    pass
            thread = getattr(sniffer, "thread", None)
            if thread is not None:
                thread.join(timeout=10)
            if thread is not None and thread.is_alive():
                raise RuntimeError("Capture thread did not stop within 10 seconds")
        except Exception as exc:
            raise RuntimeError(str(exc))

    def stop(self, conn, session_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            session = self._session
            if session is None:
                return {"active": False, "session": None}
            if session_id is not None and session_id != session["id"]:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "The requested capture session is not active.",
                )

            session["running"].clear()
            sniffer = session["sniffer"]
            if sniffer is not None:
                try:
                    self._stop_sniffer(sniffer)
                except Exception as exc:
                    session["error"] = str(exc)

            worker = session["worker"]
            if worker is not None:
                worker.join(timeout=10)

            status_value = "failed" if session["error"] else "stopped"
            self._persist_stop(session, status_value, session["error"])
            result = self.get_status()
            self._session = None
            return result

    def _persist_stop(
        self, session: dict[str, Any], status_value: str, error_message: str | None
    ) -> None:
        connection = None
        try:
            connection = psycopg2.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                dbname=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
            )
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE network_capture_sessions
                        SET status = %s,
                            stopped_at = now(),
                            packets_received = %s,
                            packets_inserted = %s,
                            packets_dropped = %s,
                            error_message = %s
                        WHERE id = %s
                        """,
                        (
                            status_value,
                            session["packets_received"],
                            session["packets_inserted"],
                            session["packets_dropped"],
                            error_message,
                            session["id"],
                        ),
                    )
        except Exception as exc:
            session["error"] = str(exc)
            logger.error("Capture session status update failed: %s", exc)
        finally:
            if connection is not None:
                connection.close()

    def shutdown(self) -> None:
        with self._lock:
            session = self._session
            if session is None:
                return
            session["running"].clear()
            if session["sniffer"] is not None:
                try:
                    self._stop_sniffer(session["sniffer"])
                except Exception:
                    pass
            worker = session["worker"]
            if worker is not None:
                worker.join(timeout=5)
            self._persist_stop(session, "stopped", None)
            self._session = None


capture_manager = CaptureManager()
