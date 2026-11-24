import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.main import app
from app.security import hash_password


PASSWORD = "Stage1!Test123"


def db_connect():
    return psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def login(client, identifier, role):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": PASSWORD,
            "role": role,
        },
    )
    if response.status_code != 200:
        raise AssertionError(
            f"Login failed for {identifier}: {response.status_code} {response.text}"
        )
    return response.json()["access_token"]


def expect(client, method, path, token, expected_status, json=None):
    response = client.request(
        method,
        path,
        headers={"Authorization": f"Bearer {token}"},
        json=json,
    )
    if response.status_code != expected_status:
        raise AssertionError(
            f"{method} {path}: got {response.status_code}, "
            f"expected {expected_status}: {response.text}"
        )
    print(f"PASS {method} {path} role_token_status={response.status_code}")


def cleanup(connection, ids):
    with connection:
        with connection.cursor() as cursor:
            if ids:
                cursor.execute(
                    "DELETE FROM audit_logs WHERE actor_user_id = ANY(%s)",
                    (list(ids.values()),),
                )
            cursor.execute(
                """
                DELETE FROM teams
                WHERE team_name IN (
                    '__stage1_http_authorized_team__',
                    '__stage1_http_other_team__'
                )
                """
            )
            cursor.execute(
                """
                DELETE FROM users
                WHERE username IN (
                    '__stage1_http_admin__',
                    '__stage1_http_lead__',
                    '__stage1_http_analyst__'
                )
                """
            )


def main():
    connection = db_connect()
    ids = {}

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM audit_logs
                    WHERE actor_user_id IN (
                        SELECT id FROM users
                        WHERE username LIKE '\\_\\_stage1\\_http\\_%'
                    )
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM teams
                    WHERE team_name IN (
                        '__stage1_http_authorized_team__',
                        '__stage1_http_other_team__'
                    )
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM users
                    WHERE username IN (
                        '__stage1_http_admin__',
                        '__stage1_http_lead__',
                        '__stage1_http_analyst__'
                    )
                    """
                )

                password_hash = hash_password(PASSWORD)
                cursor.execute(
                    """
                    INSERT INTO users
                        (username, email, full_name, password_hash, status)
                    VALUES
                        ('__stage1_http_admin__', '__stage1_http_admin@example.invalid', 'Stage 1 HTTP Admin', %s, 'active'),
                        ('__stage1_http_lead__', '__stage1_http_lead@example.invalid', 'Stage 1 HTTP Lead', %s, 'active'),
                        ('__stage1_http_analyst__', '__stage1_http_analyst@example.invalid', 'Stage 1 HTTP Analyst', %s, 'active')
                    RETURNING username, id
                    """,
                    (password_hash, password_hash, password_hash),
                )
                inserted = cursor.fetchall()
                ids.update({row["username"]: row["id"] for row in inserted})

                cursor.execute(
                    "SELECT id, role_name FROM roles WHERE role_name IN ('administrator','team_lead','security_analyst')"
                )
                roles = {row["role_name"]: row["id"] for row in cursor.fetchall()}

                cursor.executemany(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (
                        (ids["__stage1_http_admin__"], roles["administrator"]),
                        (ids["__stage1_http_lead__"], roles["team_lead"]),
                        (ids["__stage1_http_analyst__"], roles["security_analyst"]),
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO teams (team_name, description, lead_user_id)
                    VALUES
                        ('__stage1_http_authorized_team__', 'Temporary HTTP authorization test', %s),
                        ('__stage1_http_other_team__', 'Temporary HTTP authorization test', NULL)
                    RETURNING id, team_name
                    """,
                    (ids["__stage1_http_lead__"],),
                )
                teams = {row["team_name"]: row["id"] for row in cursor.fetchall()}
                cursor.execute(
                    "INSERT INTO team_members (team_id, user_id) VALUES (%s, %s)",
                    (teams["__stage1_http_authorized_team__"], ids["__stage1_http_analyst__"]),
                )

        with TestClient(app) as client:
            admin_token = login(client, "__stage1_http_admin__", "administrator")
            lead_token = login(client, "__stage1_http_lead__", "team_lead")
            analyst_token = login(client, "__stage1_http_analyst__", "security_analyst")

            admin_allowed = (
                ("GET", "/api/v1/users", 200),
                ("GET", "/api/v1/teams", 200),
                ("GET", "/api/v1/roles", 200),
                ("GET", "/api/v1/audit-logs", 200),
                ("GET", "/api/v1/network/summary", 200),
            )
            for method, path, status in admin_allowed:
                expect(client, method, path, admin_token, status)

            lead_allowed_denied = (
                ("GET", "/api/v1/users", 403),
                ("GET", "/api/v1/roles", 403),
                ("GET", "/api/v1/teams", 200),
                ("GET", "/api/v1/audit-logs", 200),
                ("GET", "/api/v1/network/summary", 200),
            )
            for method, path, status in lead_allowed_denied:
                expect(client, method, path, lead_token, status)

            analyst_allowed_denied = (
                ("GET", "/api/v1/users", 403),
                ("GET", "/api/v1/roles", 403),
                ("GET", "/api/v1/teams", 200),
                ("GET", "/api/v1/audit-logs", 403),
                ("GET", "/api/v1/network/summary", 200),
            )
            for method, path, status in analyst_allowed_denied:
                expect(client, method, path, analyst_token, status)

            expect(
                client,
                "GET",
                f"/api/v1/teams/{teams['__stage1_http_authorized_team__']}",
                lead_token,
                200,
            )
            expect(
                client,
                "GET",
                f"/api/v1/teams/{teams['__stage1_http_other_team__']}",
                lead_token,
                403,
            )
            expect(
                client,
                "GET",
                f"/api/v1/teams/{teams['__stage1_http_authorized_team__']}",
                analyst_token,
                200,
            )
            expect(
                client,
                "GET",
                f"/api/v1/teams/{teams['__stage1_http_other_team__']}",
                analyst_token,
                403,
            )

            expect(
                client,
                "PUT",
                f"/api/v1/teams/{teams['__stage1_http_other_team__']}",
                lead_token,
                403,
                {"description": "Unauthorized test update"},
            )

        print("PASS isolated HTTP role authorization checks")
    finally:
        cleanup(connection, ids)
        connection.close()
        print("PASS isolated HTTP test accounts and teams cleaned up")


if __name__ == "__main__":
    main()
