-- =====================================================================
-- NetShield AI - Module 1: User Management
-- Migration 001: Initial schema + seed roles/permissions
-- PostgreSQL 18
-- =====================================================================

BEGIN;

-- ---------- Tables ----------

CREATE TABLE IF NOT EXISTS roles (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name   VARCHAR(50)  NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permissions (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    permission_code  VARCHAR(100) NOT NULL UNIQUE,
    module           VARCHAR(50)  NOT NULL,
    description      TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       BIGINT NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    full_name     VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'inactive', 'locked')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    BIGINT      NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS teams (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_name   VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    lead_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id     BIGINT      NOT NULL REFERENCES teams(id)  ON DELETE CASCADE,
    user_id     BIGINT      NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (team_id, user_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action        VARCHAR(100) NOT NULL,
    target_type   VARCHAR(50),
    target_id     VARCHAR(100),
    status        VARCHAR(20) NOT NULL DEFAULT 'success'
                  CHECK (status IN ('success', 'failure')),
    details       JSONB,
    ip_address    VARCHAR(45),
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked    BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Indexes ----------

CREATE INDEX IF NOT EXISTS idx_users_email        ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_status       ON users (status);
CREATE INDEX IF NOT EXISTS idx_user_roles_role    ON user_roles (role_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user  ON team_members (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp    ON audit_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor        ON audit_logs (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action       ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_status       ON audit_logs (status);
CREATE INDEX IF NOT EXISTS idx_audit_target       ON audit_logs (target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_refresh_user       ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_expires    ON refresh_tokens (expires_at);

-- ---------- Seed: Roles ----------

INSERT INTO roles (role_name, description) VALUES
    ('administrator',   'Full platform access: manage users, roles, teams, permissions and audit logs.'),
    ('security_analyst','Security monitoring and investigation features assigned to them.'),
    ('team_lead',       'Oversee assigned analysts, view team activity and team-scoped audit logs.')
ON CONFLICT (role_name) DO NOTHING;

-- ---------- Seed: Permissions ----------

INSERT INTO permissions (permission_code, module, description) VALUES
    ('dashboard.view',          'dashboard',  'View dashboard statistics'),
    ('profile.manage',          'profile',    'View and update own profile, change password'),
    ('users.view',              'users',      'List and view user accounts'),
    ('users.create',            'users',      'Create user accounts'),
    ('users.update',            'users',      'Update user profile fields'),
    ('users.activate',          'users',      'Activate, deactivate or lock user accounts'),
    ('users.assign_roles',      'users',      'Assign roles to users'),
    ('roles.view',              'roles',      'View roles and permissions'),
    ('roles.manage',            'roles',      'Modify role-permission mappings'),
    ('teams.view',              'teams',      'View teams and members'),
    ('teams.create',            'teams',      'Create teams'),
    ('teams.update',            'teams',      'Update team details'),
    ('teams.delete',            'teams',      'Delete teams'),
    ('teams.manage_members',    'teams',      'Add or remove team members'),
    ('audit.view',              'audit',      'View audit logs')
ON CONFLICT (permission_code) DO NOTHING;

-- ---------- Seed: Role -> Permission mapping ----------

-- Administrator: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'administrator'
ON CONFLICT DO NOTHING;

-- Security Analyst: dashboard + own profile + view own teams
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p ON p.permission_code IN (
    'dashboard.view', 'profile.manage', 'teams.view'
)
WHERE r.role_name = 'security_analyst'
ON CONFLICT DO NOTHING;

-- Team Lead: dashboard + profile + team management (scoped in service layer) + audit view
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p ON p.permission_code IN (
    'dashboard.view', 'profile.manage',
    'teams.view', 'teams.update', 'teams.manage_members',
    'audit.view'
)
WHERE r.role_name = 'team_lead'
ON CONFLICT DO NOTHING;

COMMIT;
