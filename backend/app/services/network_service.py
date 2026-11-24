import csv
import io
import json
import shutil
import socket
import uuid
from datetime import datetime

from fastapi import HTTPException, status


LOCAL_ADDRESS_CACHE = None


def get_local_addresses():
    global LOCAL_ADDRESS_CACHE
    if LOCAL_ADDRESS_CACHE is not None:
        return LOCAL_ADDRESS_CACHE
    addresses = set()
    try:
        for address in socket.getaddrinfo(socket.gethostname(), None):
            value = address[4][0] if address[4] else None
            if value and "." in value:
                addresses.add(value)
    except Exception:
        pass
    LOCAL_ADDRESS_CACHE = addresses
    return addresses


def classify_protocol(raw_protocol, source_port, destination_port):
    raw = (raw_protocol or "").strip()
    upper = raw.upper()
    ports = {source_port, destination_port}

    if upper == "ARP" or upper.startswith("ARP"):
        return "ARP", True, "confirmed"
    if upper in {"ICMP", "ICMPV4", "ICMPV6"} or upper.startswith("ICMP"):
        return "ICMP", True, "confirmed"
    if upper == "DNS" or 53 in ports or 5353 in ports:
        return "DNS", upper == "DNS", "confirmed" if upper == "DNS" else "inferred"
    if upper in {"TLS", "TLSV1", "TLSV1.1", "TLSV1.2", "TLSV1.3", "SSL"}:
        return "HTTPS", True, "confirmed"
    if 443 in ports:
        return "HTTPS", False, "inferred"
    if upper.startswith("HTTP"):
        return "HTTP", True, "confirmed"
    if 80 in ports or 8080 in ports or 8000 in ports:
        return "HTTP", False, "inferred"
    if upper == "TCP" or upper.startswith("TCP"):
        return "TCP", True, "confirmed"
    if upper == "UDP" or upper.startswith("UDP"):
        return "UDP", True, "confirmed"
    return "Other/Unknown", False, "unknown"


def serialize_packet(row):
    protocol, confirmed, confidence = classify_protocol(
        row["protocol"], row["source_port"], row["destination_port"]
    )
    return {
        "id": row["id"],
        "packet_timestamp": row["packet_timestamp"].isoformat() if row["packet_timestamp"] else None,
        "source_ip": row["source_ip"],
        "destination_ip": row["destination_ip"],
        "source_port": row["source_port"],
        "destination_port": row["destination_port"],
        "raw_protocol": row["protocol"],
        "protocol": protocol,
        "protocol_confirmed": confirmed,
        "protocol_confidence": confidence,
        "packet_size": row["packet_size"],
        "traffic_direction": row["traffic_direction"],
        "capture_source": row.get("capture_source", "historical_import"),
    }


def get_network_summary(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) AS total_packets,
                   COALESCE(SUM(packet_size), 0) AS total_bytes
            FROM public.network_packets
        """)
        summary = cursor.fetchone()
        cursor.execute("""
            SELECT capture_source, COUNT(*) AS packet_count
            FROM public.network_packets
            GROUP BY capture_source
        """)
        source_counts = {
            row["capture_source"] or "historical_import": row["packet_count"]
            for row in cursor.fetchall()
        }
        cursor.execute("""
            SELECT id, packet_timestamp, source_ip, destination_ip,
                   source_port, destination_port, protocol,
                   packet_size, traffic_direction, capture_source
            FROM public.network_packets
            ORDER BY packet_timestamp DESC NULLS LAST, id DESC
            LIMIT 20
        """)
        recent_packets = [serialize_packet(r) for r in cursor.fetchall()]

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT source_ip, COUNT(*) AS packet_count,
                   COALESCE(SUM(packet_size), 0) AS traffic_bytes
            FROM public.network_packets
            WHERE source_ip IS NOT NULL
            GROUP BY source_ip
            ORDER BY packet_count DESC
            LIMIT 10
        """)
        top_sources = cursor.fetchall()
        cursor.execute("""
            SELECT destination_ip, COUNT(*) AS packet_count,
                   COALESCE(SUM(packet_size), 0) AS traffic_bytes
            FROM public.network_packets
            WHERE destination_ip IS NOT NULL
            GROUP BY destination_ip
            ORDER BY packet_count DESC
            LIMIT 10
        """)
        top_destinations = cursor.fetchall()

    total_packets = summary["total_packets"]
    total_bytes = summary["total_bytes"]
    return {
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "total_traffic_kb": round(total_bytes / 1024, 2),
        "total_traffic_mb": round(total_bytes / (1024 * 1024), 2),
        "average_packet_size": round(total_bytes / total_packets, 2) if total_packets else 0,
        "top_sources": top_sources,
        "top_destinations": top_destinations,
        "recent_packets": recent_packets,
        "capture_status": "historical_import_loaded",
        "data_source": "historical_import",
        "live_capture_enabled": True,
        "capture_identifier": "packet_data.csv",
        "historical_packet_count": source_counts.get("historical_import", 0),
        "live_packet_count": source_counts.get("live_capture", 0),
    }


def get_protocol_statistics(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT protocol, source_port, destination_port, packet_size
            FROM public.network_packets
        """)
        rows = cursor.fetchall()

    bucket = {}
    for row in rows:
        name, confirmed, confidence = classify_protocol(
            row["protocol"], row["source_port"], row["destination_port"]
        )
        item = bucket.setdefault(name, {
            "protocol": name,
            "packet_count": 0,
            "total_bytes": 0,
            "confirmed_count": 0,
            "inferred_count": 0,
        })
        item["packet_count"] += 1
        item["total_bytes"] += row["packet_size"] or 0
        if confidence == "confirmed":
            item["confirmed_count"] += 1
        elif confidence == "inferred":
            item["inferred_count"] += 1

    total_packets = len(rows)
    total_bytes = sum(row["packet_size"] or 0 for row in rows)
    result = []
    for name in ("TCP", "UDP", "HTTP", "HTTPS", "DNS", "ICMP", "ARP", "Other/Unknown"):
        item = bucket.get(name)
        if not item:
            continue
        item["packet_percentage"] = round(item["packet_count"] * 100 / total_packets, 2) if total_packets else 0
        item["traffic_percentage"] = round(item["total_bytes"] * 100 / total_bytes, 2) if total_bytes else 0
        result.append(item)
    return {"total_packets": total_packets, "total_bytes": total_bytes, "protocols": result}


def _packet_filter_sql(source_ip, destination_ip, ip_address, protocol,
                       source_port, destination_port, port, start_time, end_time,
                       capture_source=None):
    where = []
    params = []
    if source_ip:
        where.append("source_ip = %s"); params.append(source_ip)
    if destination_ip:
        where.append("destination_ip = %s"); params.append(destination_ip)
    if ip_address:
        where.append("(source_ip = %s OR destination_ip = %s)")
        params.extend([ip_address, ip_address])
    if protocol:
        normalized = protocol.strip().upper()
        if normalized in {"HTTPS", "TLS", "SSL"}:
            where.append(
                "(UPPER(protocol) LIKE 'TLS%' OR UPPER(protocol) LIKE 'SSL%' "
                "OR source_port = 443 OR destination_port = 443)"
            )
        elif normalized == "HTTP":
            where.append(
                "(UPPER(protocol) LIKE 'HTTP%' "
                "OR source_port IN (80, 8080, 8000) "
                "OR destination_port IN (80, 8080, 8000))"
            )
        elif normalized in {"TCP", "UDP", "DNS", "ARP", "ICMP"}:
            if normalized == "DNS":
                where.append(
                    "(UPPER(protocol) LIKE 'DNS%' "
                    "OR source_port IN (53, 5353) "
                    "OR destination_port IN (53, 5353))"
                )
            elif normalized == "ARP":
                where.append("UPPER(protocol) LIKE 'ARP%'")
            elif normalized == "ICMP":
                where.append("UPPER(protocol) LIKE 'ICMP%'")
            else:
                where.append("UPPER(protocol) LIKE %s")
                params.append(f"{normalized}%")
        else:
            where.append("protocol ILIKE %s"); params.append(f"%{protocol}%")
    if source_port is not None:
        where.append("source_port = %s"); params.append(source_port)
    if destination_port is not None:
        where.append("destination_port = %s"); params.append(destination_port)
    if port is not None:
        where.append("(source_port = %s OR destination_port = %s)")
        params.extend([port, port])
    if start_time:
        try:
            datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid start_time")
        where.append("packet_timestamp >= %s"); params.append(start_time)
    if end_time:
        try:
            datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid end_time")
        where.append("packet_timestamp <= %s"); params.append(end_time)
    if capture_source and capture_source != "combined":
        where.append("capture_source = %s"); params.append(capture_source)
    return ("WHERE " + " AND ".join(where) if where else ""), params


def get_packets(conn, source_ip, destination_ip, ip_address, protocol,
                source_port, destination_port, port, start_time, end_time,
                page, page_size, capture_source=None):
    where_sql, params = _packet_filter_sql(
        source_ip, destination_ip, ip_address, protocol,
        source_port, destination_port, port, start_time, end_time,
        capture_source,
    )
    with conn.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) AS total FROM public.network_packets {where_sql}",
            params if params else None,
        )
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"""
            SELECT id, packet_timestamp, source_ip, destination_ip,
                   source_port, destination_port, protocol,
                   packet_size, traffic_direction, capture_source
            FROM public.network_packets
            {where_sql}
            ORDER BY packet_timestamp DESC NULLS LAST, id DESC
            LIMIT {page_size} OFFSET {(page - 1) * page_size}
            """,
            params if params else None,
        )
        items = [serialize_packet(r) for r in cursor.fetchall()]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


PACKET_CSV_COLUMNS = (
    "id",
    "packet_timestamp",
    "source_ip",
    "source_port",
    "destination_ip",
    "destination_port",
    "raw_protocol",
    "protocol",
    "protocol_confirmed",
    "protocol_confidence",
    "packet_size",
    "traffic_direction",
    "capture_id",
    "frame_number",
    "capture_source",
)


def _csv_safe_value(value):
    if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _packet_csv_row(row):
    protocol, _, _ = classify_protocol(
        row["protocol"], row["source_port"], row["destination_port"]
    )
    timestamp = row["packet_timestamp"]
    return [
        row["id"],
        timestamp.isoformat() if timestamp else None,
        row["source_ip"],
        row["source_port"],
        row["destination_ip"],
        row["destination_port"],
        row["protocol"],
        protocol,
        row["protocol_confirmed"],
        row["protocol_confidence"],
        row["packet_size"],
        row["traffic_direction"],
        row["capture_id"],
        row["frame_number"],
        row["capture_source"] or "historical_import",
    ]


def iter_packet_csv(conn, source_ip=None, destination_ip=None, ip_address=None,
                    protocol=None, source_port=None, destination_port=None,
                    port=None, start_time=None, end_time=None,
                    capture_source="combined"):
    where_sql, params = _packet_filter_sql(
        source_ip, destination_ip, ip_address, protocol,
        source_port, destination_port, port, start_time, end_time,
        capture_source,
    )
    query = f"""
        SELECT id, packet_timestamp, source_ip, source_port,
               destination_ip, destination_port, protocol,
               protocol_confirmed, protocol_confidence, packet_size,
               traffic_direction, capture_id, frame_number, capture_source
        FROM public.network_packets
        {where_sql}
        ORDER BY packet_timestamp DESC NULLS LAST, id DESC
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    with conn.cursor(name=f"netshield_packet_export_{uuid.uuid4().hex}") as cursor:
        cursor.itersize = 1000
        cursor.execute(query, params if params else None)
        writer.writerow(PACKET_CSV_COLUMNS)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        while rows := cursor.fetchmany(1000):
            for row in rows:
                writer.writerow(_csv_safe_value(value) for value in _packet_csv_row(row))
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)


def get_ip_statistics(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT source_ip AS ip, COUNT(*) AS packet_count,
                   COALESCE(SUM(packet_size), 0) AS traffic_bytes,
                   'source' AS role
            FROM public.network_packets
            WHERE source_ip IS NOT NULL
            GROUP BY source_ip
        """)
        sources = cursor.fetchall()
        cursor.execute("""
            SELECT destination_ip AS ip, COUNT(*) AS packet_count,
                   COALESCE(SUM(packet_size), 0) AS traffic_bytes,
                   'destination' AS role
            FROM public.network_packets
            WHERE destination_ip IS NOT NULL
            GROUP BY destination_ip
        """)
        destinations = cursor.fetchall()
    return {
        "source_ips": sorted(sources, key=lambda r: r["packet_count"], reverse=True)[:20],
        "destination_ips": sorted(destinations, key=lambda r: r["packet_count"], reverse=True)[:20],
    }


def get_direction_statistics(conn):
    local_addresses = get_local_addresses()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT packet_timestamp, source_ip, destination_ip, packet_size
            FROM public.network_packets
        """)
        rows = cursor.fetchall()

    counts = {"incoming": 0, "outgoing": 0, "unknown": 0}
    bytes_by_direction = {"incoming": 0, "outgoing": 0, "unknown": 0}
    for row in rows:
        source = row["source_ip"]
        destination = row["destination_ip"]
        if destination in local_addresses and source not in local_addresses:
            direction = "incoming"
        elif source in local_addresses and destination not in local_addresses:
            direction = "outgoing"
        else:
            direction = "unknown"
        counts[direction] += 1
        bytes_by_direction[direction] += row["packet_size"] or 0
    return {
        "local_addresses": sorted(local_addresses),
        "packet_counts": counts,
        "traffic_bytes": bytes_by_direction,
    }


def get_timeline(conn, bucket, start_time, end_time):
    formats = {"minute": "1 minute", "hour": "1 hour", "day": "1 day"}
    interval = formats[bucket]
    where = []
    params = []
    if start_time:
        where.append("packet_timestamp >= %s"); params.append(start_time)
    if end_time:
        where.append("packet_timestamp <= %s"); params.append(end_time)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    local_addresses = get_local_addresses()
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT packet_timestamp, source_ip, destination_ip, packet_size
            FROM public.network_packets
            {where_sql}
            ORDER BY packet_timestamp
            """,
            params if params else None,
        )
        rows = cursor.fetchall()

    buckets = {}
    for row in rows:
        timestamp = row["packet_timestamp"]
        if timestamp is None:
            continue
        if bucket == "minute":
            key = timestamp.replace(second=0, microsecond=0)
        elif bucket == "hour":
            key = timestamp.replace(minute=0, second=0, microsecond=0)
        else:
            key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        item = buckets.setdefault(key, {
            "timestamp": key.isoformat(),
            "packet_count": 0,
            "traffic_bytes": 0,
            "incoming_packets": 0,
            "outgoing_packets": 0,
            "unknown_packets": 0,
        })
        item["packet_count"] += 1
        item["traffic_bytes"] += row["packet_size"] or 0
        if row["destination_ip"] in local_addresses and row["source_ip"] not in local_addresses:
            item["incoming_packets"] += 1
        elif row["source_ip"] in local_addresses and row["destination_ip"] not in local_addresses:
            item["outgoing_packets"] += 1
        else:
            item["unknown_packets"] += 1
    return {"bucket": interval, "items": list(buckets.values())}


def get_alert_status():
    return {
        "implemented": False,
        "alerts": [],
        "message": "Attack detection has not been implemented. No alert claims are displayed.",
    }


def get_system_status():
    cpu = memory = disk = network_io = None
    try:
        import psutil
        cpu = round(psutil.cpu_percent(interval=None), 2)
        memory = round(psutil.virtual_memory().percent, 2)
        disk = round(psutil.disk_usage("/").percent, 2)
        counters = psutil.net_io_counters()
        network_io = {
            "bytes_sent": counters.bytes_sent,
            "bytes_received": counters.bytes_recv,
        }
    except ImportError:
        pass
    return {
        "cpu_usage_percent": cpu,
        "memory_usage_percent": memory,
        "disk_usage_percent": disk,
        "network_io": network_io,
    }


def build_report(conn):
    summary = get_network_summary(conn)
    protocols = get_protocol_statistics(conn)
    ips = get_ip_statistics(conn)
    directions = get_direction_statistics(conn)
    return json.dumps({
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data_source": "historical_import",
        "live_capture_enabled": False,
        "summary": summary,
        "protocols": protocols,
        "ip_statistics": ips,
        "traffic_directions": directions,
        "alerts": get_alert_status(),
    }, indent=2, default=str)
