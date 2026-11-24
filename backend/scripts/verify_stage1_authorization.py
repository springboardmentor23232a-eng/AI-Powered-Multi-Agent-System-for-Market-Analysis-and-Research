import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.dependencies import CurrentUser, require_permissions
from app.services import audit_service_query, team_service


def permission_test(user, permission, expected_allowed):
    checker = require_permissions(permission)
    try:
        checker(user=user)
        allowed = True
    except HTTPException as exc:
        allowed = exc.status_code != 403

    if allowed != expected_allowed:
        raise AssertionError(
            f"{user.username}: {permission} allowed={allowed}, expected={expected_allowed}"
        )
    print(
        f"PASS permission={permission} role={','.join(user.roles)} "
        f"allowed={allowed}"
    )


def main():
    connection = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        cursor_factory=RealDictCursor,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.role_name, p.permission_code
                FROM roles r
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE r.role_name IN ('administrator', 'team_lead', 'security_analyst')
                ORDER BY r.role_name, p.permission_code
                """
            )
            role_permissions = {}
            for row in cursor.fetchall():
                role_permissions.setdefault(row["role_name"], set()).add(
                    row["permission_code"]
                )

        if not role_permissions:
            raise AssertionError("No role permissions found. Database migrations are not applied.")

        administrator = CurrentUser(
            id=-101,
            username="stage1_admin",
            email="stage1_admin@example.invalid",
            full_name="Stage 1 Administrator",
            status="active",
            roles=["administrator"],
            permissions=set(role_permissions.get("administrator", set())),
        )
        team_lead = CurrentUser(
            id=-102,
            username="stage1_lead",
            email="stage1_lead@example.invalid",
            full_name="Stage 1 Team Lead",
            status="active",
            roles=["team_lead"],
            permissions=set(role_permissions.get("team_lead", set())),
        )
        analyst = CurrentUser(
            id=-103,
            username="stage1_analyst",
            email="stage1_analyst@example.invalid",
            full_name="Stage 1 Analyst",
            status="active",
            roles=["security_analyst"],
            permissions=set(role_permissions.get("security_analyst", set())),
        )

        permissions = (
            "users.view",
            "users.create",
            "teams.view",
            "teams.manage_members",
            "roles.view",
            "audit.view",
            "network.view",
            "network.analyze",
            "reports.generate",
        )
        expected_roles = {
            "users.view": {"administrator"},
            "users.create": {"administrator"},
            "teams.view": {"administrator", "team_lead", "security_analyst"},
            "teams.manage_members": {"administrator", "team_lead"},
            "roles.view": {"administrator"},
            "audit.view": {"administrator", "team_lead"},
            "network.view": {"administrator", "team_lead", "security_analyst"},
            "network.analyze": {"administrator", "security_analyst"},
            "reports.generate": {"administrator", "team_lead", "security_analyst"},
        }

        for permission in permissions:
            for user in (administrator, team_lead, analyst):
                allowed_roles = expected_roles[permission]
                permission_test(
                    user,
                    permission,
                    user.roles[0] in allowed_roles,
                )

        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                    (username, email, full_name, password_hash, status)
                VALUES
                    ('__stage1_lead__', '__stage1_lead@example.invalid', 'Stage 1 Lead', 'not-used', 'active'),
                    ('__stage1_analyst__', '__stage1_analyst@example.invalid', 'Stage 1 Analyst', 'not-used', 'active')
                RETURNING id, username
                """
            )
            lead_row, analyst_row = cursor.fetchall()
            cursor.execute(
                """
                INSERT INTO teams (team_name, description, lead_user_id)
                VALUES
                    ('__stage1_authorized_team__', 'Temporary authorization test', %s),
                    ('__stage1_other_team__', 'Temporary authorization test', NULL)
                RETURNING id, team_name
                """,
                (lead_row["id"],),
            )
            authorized_team, other_team = cursor.fetchall()
            cursor.execute(
                "INSERT INTO team_members (team_id, user_id) VALUES (%s, %s)",
                (authorized_team["id"], analyst_row["id"]),
            )

            lead = CurrentUser(
                id=lead_row["id"],
                username=lead_row["username"],
                email="__stage1_lead@example.invalid",
                full_name="Stage 1 Lead",
                status="active",
                roles=["team_lead"],
                permissions=set(role_permissions.get("team_lead", set())),
            )
            analyst_db = CurrentUser(
                id=analyst_row["id"],
                username=analyst_row["username"],
                email="__stage1_analyst@example.invalid",
                full_name="Stage 1 Analyst",
                status="active",
                roles=["security_analyst"],
                permissions=set(role_permissions.get("security_analyst", set())),
            )

            authorized = team_service.get_team(
                connection, authorized_team["id"], lead
            )
            print(f"PASS team_lead authorized_team={authorized['team_name']}")

            try:
                team_service.get_team(connection, other_team["id"], lead)
            except HTTPException as exc:
                if exc.status_code != 403:
                    raise
                print("PASS team_lead denied_other_team=403")
            else:
                raise AssertionError("Team Lead accessed a team outside the authorized scope.")

            analyst_team = team_service.get_team(
                connection, authorized_team["id"], analyst_db
            )
            print(f"PASS security_analyst team_view={analyst_team['team_name']}")

            try:
                team_service.get_team(connection, other_team["id"], analyst_db)
            except HTTPException as exc:
                if exc.status_code != 403:
                    raise
                print("PASS security_analyst denied_other_team=403")
            else:
                raise AssertionError("Security Analyst accessed a team outside membership.")

        connection.rollback()
        print("PASS isolated database test data rolled back")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
