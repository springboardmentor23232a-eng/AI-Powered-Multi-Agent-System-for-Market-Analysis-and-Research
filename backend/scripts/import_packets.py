
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import sys

import psycopg2
from psycopg2.extras import execute_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings

# Locate the CSV in the main NetShield AI folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = PROJECT_ROOT / "packet_data.csv"


def get_value(row, *fields):
    for field in fields:
        value = row.get(field, "").strip()
        if value:
            return value
    return None


def to_int(value):
    return int(value) if value else None


def make_import_key(capture_id, frame_number, packet_time, source_ip, destination_ip,
                   source_port, destination_port, protocol, packet_size, legacy_id=None):
    if legacy_id is not None:
        payload = (
            f"legacy_packet_data_csv|{legacy_id}|{packet_time.strftime('%Y-%m-%d %H:%M:%S.%f')}|"
            f"{source_ip or ''}|{destination_ip or ''}|{source_port or ''}|"
            f"{destination_port or ''}|{protocol or ''}|{packet_size or ''}"
        )
    else:
        payload = (
            f"{capture_id}|{frame_number}|{packet_time.isoformat()}|"
            f"{source_ip or ''}|{destination_ip or ''}|{source_port or ''}|"
            f"{destination_port or ''}|{protocol or ''}|{packet_size or ''}"
        )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_FILE}")

    records = []

    with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for index, row in enumerate(reader, start=1):
            timestamp = row.get("frame.time_epoch", "").strip()
            if not timestamp:
                continue

            packet_time = datetime.fromtimestamp(
                float(timestamp), tz=timezone.utc
            ).replace(tzinfo=None)

            source_ip = get_value(row, "ip.src", "ipv6.src")
            destination_ip = get_value(row, "ip.dst", "ipv6.dst")
            source_port = to_int(get_value(row, "tcp.srcport", "udp.srcport"))
            destination_port = to_int(get_value(row, "tcp.dstport", "udp.dstport"))
            protocol = row.get("_ws.col.protocol", "").strip() or "Unknown"
            packet_size = to_int(row.get("frame.len", "").strip())

            import_key = make_import_key(
                "packet_data.csv",
                index,
                packet_time,
                source_ip,
                destination_ip,
                source_port,
                destination_port,
                protocol,
                packet_size,
                legacy_id=index,
            )

            records.append((
                packet_time,
                source_ip,
                destination_ip,
                source_port,
                destination_port,
                protocol,
                packet_size,
                "legacy_packet_data_csv",
                index,
                False,
                "confirmed" if protocol.upper() in {"ARP", "TCP", "UDP", "DNS", "TLSV1.2"} else "unknown",
                "unknown",
                import_key,
            ))

    if not records:
        print("No valid packet records found.")
        return

    connection = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
    )

    try:
        before_count = 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS packet_count FROM public.network_packets")
            before_count = cursor.fetchone()[0]

        with connection:
            with connection.cursor() as cursor:
                records_to_insert = []
                for record in records:
                    cursor.execute(
                        """
                        SELECT 1
                        FROM public.network_packets
                        WHERE packet_timestamp = %s
                          AND source_ip IS NOT DISTINCT FROM %s
                          AND destination_ip IS NOT DISTINCT FROM %s
                          AND source_port IS NOT DISTINCT FROM %s
                          AND destination_port IS NOT DISTINCT FROM %s
                          AND protocol IS NOT DISTINCT FROM %s
                          AND packet_size IS NOT DISTINCT FROM %s
                        LIMIT 1
                        """,
                        (record[0], record[1], record[2], record[3], record[4], record[5], record[6]),
                    )
                    if cursor.fetchone() is None:
                        records_to_insert.append(record)

                query = """
                    INSERT INTO public.network_packets (
                        packet_timestamp,
                        source_ip,
                        destination_ip,
                        source_port,
                        destination_port,
                        protocol,
                        packet_size,
                        capture_id,
                        frame_number,
                        protocol_confirmed,
                        protocol_confidence,
                        traffic_direction,
                        import_key
                    )
                    VALUES %s
                    ON CONFLICT (import_key) DO NOTHING
                """
                if records_to_insert:
                    execute_values(cursor, query, records_to_insert, page_size=1000)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS packet_count FROM public.network_packets")
            after_count = cursor.fetchone()[0]

        print(
            f"Capture import complete: {len(records)} source rows inspected, "
            f"{after_count - before_count} rows inserted, "
            f"{len(records) - (after_count - before_count)} duplicate rows skipped."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
