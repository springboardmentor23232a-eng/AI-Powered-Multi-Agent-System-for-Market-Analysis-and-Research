from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from ..config import settings
from . import audit_service


def _serialize_alert(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "rule_name": row["rule_name"],
        "severity": row["severity"],
        "status": row["status"],
        "source_ip": row["source_ip"],
        "destination_ip": row["destination_ip"],
        "capture_source": row["capture_source"],
        "capture_id": row["capture_id"],
        "observed_count": row["observed_count"],
        "threshold_value": row["threshold_value"],
        "window_seconds": row["window_seconds"],
        "explanation": row["explanation"],
        "detected_at": row["detected_at"].isoformat() if row["detected_at"] else None,
        "acknowledged_at": row["acknowledged_at"].isoformat() if row["acknowledged_at"] else None,
        "acknowledged_by": row["acknowledged_by"],
        "resolved_at": row["resolved_at"].isoformat() if row["resolved_at"] else None,
        "resolved_by": row["resolved_by"],
    }


def _create_alert_if_not_recent(
    conn,
    rule_name: str,
    severity: str,
    source_ip: str | None,
    destination_ip: str | None,
    capture_source: str,
    capture_id: str | None,
    observed_count: int,
    threshold_value: int,
    window_seconds: int,
    explanation: str,
) -> dict[str, Any] | None:
    dedupe_key = "|".join([
        rule_name,
        source_ip or "",
        capture_source,
        capture_id or "",
    ])
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM network_alerts
            WHERE dedupe_key = %s
              AND detected_at >= now() - (%s * INTERVAL '1 minute')
            LIMIT 1
            """,
            (dedupe_key, settings.DETECTION_ALERT_COOLDOWN_MINUTES),
        )
        if cursor.fetchone():
            return None
        cursor.execute(
            """
            INSERT INTO network_alerts (
                rule_name, severity, status, source_ip, destination_ip,
                capture_source, capture_id, observed_count, threshold_value,
                window_seconds, explanation, dedupe_key
            )
            VALUES (%s, %s, 'open', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                rule_name,
                severity,
                source_ip,
                destination_ip,
                capture_source,
                capture_id,
                observed_count,
                threshold_value,
                window_seconds,
                explanation,
                dedupe_key,
            ),
        )
        row = cursor.fetchone()
    conn.commit()
    return _serialize_alert(row)


def evaluate_packets(
    conn,
    capture_source: str = "live_capture",
    capture_id: str | None = None,
) -> dict[str, Any]:
    if capture_source not in {"historical_import", "live_capture"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid capture source")

    created: list[dict[str, Any]] = []
    window_seconds = max(
        settings.DETECTION_HIGH_VOLUME_WINDOW_SECONDS,
        settings.DETECTION_PORT_CONCENTRATION_WINDOW_SECONDS,
    )

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT MAX(packet_timestamp) AS latest
            FROM public.network_packets
            WHERE capture_source = %s
              AND packet_timestamp IS NOT NULL
              AND (%s IS NULL OR capture_id = %s)
            """,
            (capture_source, capture_id, capture_id),
        )
        latest = cursor.fetchone()["latest"]
    if latest is None:
        return {"created": [], "created_count": 0, "evaluated_capture_source": capture_source}

    if isinstance(latest, str):
        latest = datetime.fromisoformat(latest)
    window_start = latest - timedelta(seconds=window_seconds)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT source_ip, COUNT(*) AS observed_count
            FROM public.network_packets
            WHERE capture_source = %s
              AND packet_timestamp >= %s
              AND packet_timestamp <= %s
              AND source_ip IS NOT NULL
              AND (%s IS NULL OR capture_id = %s)
            GROUP BY source_ip
            HAVING COUNT(*) >= %s
            ORDER BY observed_count DESC
            """,
            (
                capture_source,
                window_start,
                latest,
                capture_id,
                capture_id,
                settings.DETECTION_HIGH_VOLUME_THRESHOLD,
            ),
        )
        volume_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT source_ip,
                   COUNT(DISTINCT destination_port) AS observed_count
            FROM public.network_packets
            WHERE capture_source = %s
              AND packet_timestamp >= %s
              AND packet_timestamp <= %s
              AND source_ip IS NOT NULL
              AND destination_port IS NOT NULL
              AND (%s IS NULL OR capture_id = %s)
            GROUP BY source_ip
            HAVING COUNT(DISTINCT destination_port) >= %s
            ORDER BY observed_count DESC
            """,
            (
                capture_source,
                window_start,
                latest,
                capture_id,
                capture_id,
                settings.DETECTION_PORT_CONCENTRATION_THRESHOLD,
            ),
        )
        port_rows = cursor.fetchall()

    for row in volume_rows:
        source_ip = row["source_ip"]
        observed = int(row["observed_count"])
        threshold = settings.DETECTION_HIGH_VOLUME_THRESHOLD
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT destination_ip, COUNT(*) AS count
                FROM public.network_packets
                WHERE capture_source = %s
                  AND source_ip = %s
                  AND packet_timestamp >= %s
                  AND packet_timestamp <= %s
                  AND destination_ip IS NOT NULL
                  AND (%s IS NULL OR capture_id = %s)
                GROUP BY destination_ip
                ORDER BY count DESC
                LIMIT 1
                """,
                (
                    capture_source,
                    source_ip,
                    window_start,
                    latest,
                    capture_id,
                    capture_id,
                ),
            )
            top_destination = cursor.fetchone()
        destination_ip = top_destination["destination_ip"] if top_destination else None
        alert = _create_alert_if_not_recent(
            conn,
            "High Packet Volume",
            "medium",
            source_ip,
            destination_ip,
            capture_source,
            capture_id,
            observed,
            threshold,
            settings.DETECTION_HIGH_VOLUME_WINDOW_SECONDS,
            (
                f"Source IP {source_ip} produced {observed} packets in "
                f"{settings.DETECTION_HIGH_VOLUME_WINDOW_SECONDS} seconds, "
                f"exceeding the configured threshold of {threshold}. "
                "This is a heuristic signal, not proof of an attack."
            ),
        )
        if alert:
            created.append(alert)

    for row in port_rows:
        source_ip = row["source_ip"]
        observed = int(row["observed_count"])
        threshold = settings.DETECTION_PORT_CONCENTRATION_THRESHOLD
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT destination_ip, COUNT(*) AS count
                FROM public.network_packets
                WHERE capture_source = %s
                  AND source_ip = %s
                  AND destination_port IS NOT NULL
                  AND packet_timestamp >= %s
                  AND packet_timestamp <= %s
                  AND destination_ip IS NOT NULL
                  AND (%s IS NULL OR capture_id = %s)
                GROUP BY destination_ip
                ORDER BY count DESC
                LIMIT 1
                """,
                (
                    capture_source,
                    source_ip,
                    window_start,
                    latest,
                    capture_id,
                    capture_id,
                ),
            )
            top_destination = cursor.fetchone()
        destination_ip = top_destination["destination_ip"] if top_destination else None
        alert = _create_alert_if_not_recent(
            conn,
            "Port Concentration",
            "medium",
            source_ip,
            destination_ip,
            capture_source,
            capture_id,
            observed,
            threshold,
            settings.DETECTION_PORT_CONCENTRATION_WINDOW_SECONDS,
            (
                f"Source IP {source_ip} used {observed} distinct destination ports "
                f"in {settings.DETECTION_PORT_CONCENTRATION_WINDOW_SECONDS} seconds, "
                f"exceeding the configured threshold of {threshold}. "
                "This is a heuristic signal, not proof of an attack."
            ),
        )
        if alert:
            created.append(alert)

    return {
        "created": created,
        "created_count": len(created),
        "evaluated_capture_source": capture_source,
        "capture_id": capture_id,
    }


def list_alerts(conn, severity, status_filter, rule_name, capture_source, page, page_size):
    where = []
    params = []
    if severity:
        where.append("severity = %s"); params.append(severity)
    if status_filter:
        where.append("status = %s"); params.append(status_filter)
    if rule_name:
        where.append("rule_name = %s"); params.append(rule_name)
    if capture_source:
        where.append("capture_source = %s"); params.append(capture_source)
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    with conn.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) AS total FROM network_alerts {where_sql}",
            params if params else None,
        )
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"""
            SELECT * FROM network_alerts
            {where_sql}
            ORDER BY detected_at DESC, id DESC
            LIMIT {page_size} OFFSET {(page - 1) * page_size}
            """,
            params if params else None,
        )
        items = [_serialize_alert(row) for row in cursor.fetchall()]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_alert(conn, alert_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM network_alerts WHERE id = %s", (alert_id,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return _serialize_alert(row)


def get_summary(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM network_alerts"
        )
        total = cursor.fetchone()["total"]
        cursor.execute(
            """
            SELECT severity, COUNT(*) AS count
            FROM network_alerts
            GROUP BY severity
            """
        )
        by_severity = {row["severity"]: row["count"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM network_alerts
            GROUP BY status
            """
        )
        by_status = {row["status"]: row["count"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT * FROM network_alerts
            ORDER BY detected_at DESC, id DESC
            LIMIT 5
            """
        )
        recent = [_serialize_alert(row) for row in cursor.fetchall()]
    return {
        "total": total,
        "by_severity": by_severity,
        "by_status": by_status,
        "recent": recent,
    }


def acknowledge_alert(conn, alert_id, actor, ip):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE network_alerts
            SET status = 'acknowledged',
                acknowledged_at = now(),
                acknowledged_by = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (actor.id, alert_id),
        )
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    audit_service.log(
        conn,
        actor_user_id=actor.id,
        action="alert.acknowledge",
        target_type="network_alert",
        target_id=str(alert_id),
        ip_address=ip,
    )
    conn.commit()
    return _serialize_alert(row)


def resolve_alert(conn, alert_id, actor, ip):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE network_alerts
            SET status = 'resolved',
                resolved_at = now(),
                resolved_by = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (actor.id, alert_id),
        )
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    audit_service.log(
        conn,
        actor_user_id=actor.id,
        action="alert.resolve",
        target_type="network_alert",
        target_id=str(alert_id),
        ip_address=ip,
    )
    conn.commit()
    return _serialize_alert(row)
