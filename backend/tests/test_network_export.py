import csv
import io
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.dependencies import CurrentUser, get_current_user
from app.main import app
from app.services import network_service


def packet_row(
    packet_id=1,
    timestamp="2025-01-02T03:04:05+00:00",
    capture_source="historical_import",
):
    from datetime import datetime

    return {
        "id": packet_id,
        "packet_timestamp": datetime.fromisoformat(timestamp),
        "source_ip": "192.0.2.10",
        "source_port": 43210,
        "destination_ip": "198.51.100.8",
        "destination_port": 443,
        "protocol": "TCP",
        "protocol_confirmed": True,
        "protocol_confidence": "confirmed",
        "packet_size": 512,
        "traffic_direction": "outgoing",
        "capture_id": "capture-1",
        "frame_number": packet_id,
        "capture_source": capture_source,
    }


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.offset = 0
        self.query = None
        self.params = None
        self.fetch_sizes = []
        self.itersize = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchmany(self, size):
        self.fetch_sizes.append(size)
        batch = self.rows[self.offset:self.offset + size]
        self.offset += len(batch)
        return batch


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self, name=None):
        return self.cursor_instance


class PacketCsvTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_csv_has_metadata_and_source_without_payload(self):
        rows = [
            packet_row(capture_source="historical_import"),
            packet_row(packet_id=2, capture_source="live_capture"),
        ]
        connection = FakeConnection(rows)
        content = "".join(network_service.iter_packet_csv(connection))
        parsed = list(csv.DictReader(io.StringIO(content)))

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["raw_protocol"], "TCP")
        self.assertEqual(parsed[0]["protocol"], "HTTPS")
        self.assertEqual(parsed[0]["capture_source"], "historical_import")
        self.assertEqual(parsed[1]["capture_source"], "live_capture")
        self.assertEqual(parsed[0]["packet_size"], "512")
        self.assertNotIn("payload", parsed[0])
        self.assertNotIn("application_data", parsed[0])
        self.assertTrue(connection.cursor_instance.query.lstrip().startswith("SELECT"))

    def test_filters_are_bound_and_capture_source_is_applied(self):
        connection = FakeConnection([])
        content = "".join(
            network_service.iter_packet_csv(
                connection,
                source_ip="192.0.2.10",
                destination_ip="198.51.100.8",
                ip_address="192.0.2.10",
                source_port=43210,
                destination_port=443,
                port=443,
                protocol="HTTPS",
                start_time="2025-01-01T00:00:00Z",
                end_time="2025-02-01T00:00:00Z",
                capture_source="live_capture",
            )
        )

        self.assertEqual(len(list(csv.reader(io.StringIO(content)))), 1)
        cursor = connection.cursor_instance
        self.assertIn("source_ip = %s", cursor.query)
        self.assertIn("destination_ip = %s", cursor.query)
        self.assertIn("(source_ip = %s OR destination_ip = %s)", cursor.query)
        self.assertIn("capture_source = %s", cursor.query)
        self.assertIn("source_port = %s", cursor.query)
        self.assertIn("destination_port = %s", cursor.query)
        self.assertIn("(source_port = %s OR destination_port = %s)", cursor.query)
        self.assertIn("packet_timestamp >= %s", cursor.query)
        self.assertIn("packet_timestamp <= %s", cursor.query)
        self.assertIn("OR source_port = 443", cursor.query)
        self.assertNotIn("LIMIT", cursor.query)
        self.assertEqual(
            cursor.params,
            [
                "192.0.2.10",
                "198.51.100.8",
                "192.0.2.10",
                "192.0.2.10",
                43210,
                443,
                443,
                443,
                "2025-01-01T00:00:00Z",
                "2025-02-01T00:00:00Z",
                "live_capture",
            ],
        )

    def test_source_selection_supports_historical_live_and_combined(self):
        for source, should_filter in (
            ("historical_import", True),
            ("live_capture", True),
            ("combined", False),
        ):
            with self.subTest(source=source):
                connection = FakeConnection([])
                list(network_service.iter_packet_csv(connection, capture_source=source))
                cursor = connection.cursor_instance
                self.assertEqual("capture_source = %s" in cursor.query, should_filter)
                if should_filter:
                    self.assertEqual(cursor.params, [source])
                else:
                    self.assertIsNone(cursor.params)

    def test_empty_export_contains_header_only(self):
        content = "".join(network_service.iter_packet_csv(FakeConnection([])))
        self.assertEqual(
            list(csv.reader(io.StringIO(content))),
            [list(network_service.PACKET_CSV_COLUMNS)],
        )

    def test_large_export_fetches_in_bounded_batches(self):
        rows = [packet_row(packet_id=index) for index in range(2505)]
        connection = FakeConnection(rows)
        chunks = list(network_service.iter_packet_csv(connection))

        self.assertEqual(len(chunks), 4)
        self.assertEqual(connection.cursor_instance.fetch_sizes, [1000, 1000, 1000, 1000])
        self.assertEqual(
            len(list(csv.DictReader(io.StringIO("".join(chunks))))),
            2505,
        )

    def test_formula_like_text_is_safe_for_spreadsheet_consumers(self):
        row = packet_row()
        row["protocol"] = " =1+1"
        content = "".join(network_service.iter_packet_csv(FakeConnection([row])))
        parsed = list(csv.DictReader(io.StringIO(content)))
        self.assertEqual(parsed[0]["raw_protocol"], "' =1+1")

    def test_report_json_shape_remains_compatible(self):
        with (
            patch.object(network_service, "get_network_summary", return_value={"total_packets": 1}),
            patch.object(network_service, "get_protocol_statistics", return_value={"protocols": []}),
            patch.object(network_service, "get_ip_statistics", return_value={"source_ips": []}),
            patch.object(network_service, "get_direction_statistics", return_value={"packet_counts": {}}),
            patch.object(network_service, "get_alert_status", return_value={"implemented": False}),
        ):
            payload = json.loads(network_service.build_report(None))

        self.assertEqual(
            set(payload),
            {
                "generated_at",
                "data_source",
                "live_capture_enabled",
                "summary",
                "protocols",
                "ip_statistics",
                "traffic_directions",
                "alerts",
            },
        )

    def test_csv_export_uses_existing_report_permission_for_each_role(self):
        users = (
            CurrentUser(1, "admin", "", "", "active", ["administrator"], set()),
            CurrentUser(2, "analyst", "", "", "active", ["security_analyst"], {"reports.generate"}),
            CurrentUser(3, "lead", "", "", "active", ["team_lead"], {"reports.generate"}),
        )
        for user in users:
            with self.subTest(role=user.roles[0]):
                app.dependency_overrides[get_current_user] = lambda user=user: user
                connection = FakeConnection([])
                with (
                    patch("app.routers.network.database.get_connection", return_value=connection),
                    patch("app.routers.network.database.put_connection"),
                ):
                    response = TestClient(app).get(
                        "/api/v1/network/packets/export.csv",
                        headers={"Authorization": "Bearer test-token"},
                    )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
                self.assertIn("capture_source", response.text)

    def test_csv_export_denies_users_without_report_permission(self):
        user = CurrentUser(4, "viewer", "", "", "active", ["security_analyst"], set())
        app.dependency_overrides[get_current_user] = lambda: user
        response = TestClient(app).get("/api/v1/network/packets/export.csv")
        self.assertEqual(response.status_code, 403)

    def test_csv_export_requires_authentication(self):
        from fastapi import HTTPException

        def unauthenticated():
            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user] = unauthenticated
        response = TestClient(app).get("/api/v1/network/packets/export.csv")
        self.assertEqual(response.status_code, 401)

    def test_json_report_download_route_is_unchanged(self):
        user = CurrentUser(2, "analyst", "", "", "active", ["security_analyst"], {"reports.generate"})
        app.dependency_overrides[get_current_user] = lambda: user
        report = '{"data_source":"historical_import"}'
        with patch("app.routers.network.network_service.build_report", return_value=report):
            response = TestClient(app).get("/api/v1/network/report")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIn("netshield-network-report.json", response.headers["content-disposition"])
        self.assertEqual(response.text, report)


if __name__ == "__main__":
    unittest.main()
