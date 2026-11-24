-- NetShield AI - Stage 4: Deterministic network alert storage
-- Additive only. No packet or historical data is changed.

BEGIN;

INSERT INTO permissions (permission_code, module, description) VALUES
    ('alerts.view', 'alerts', 'View network detection alerts'),
    ('alerts.manage', 'alerts', 'Acknowledge, resolve and evaluate network detection alerts')
ON CONFLICT (permission_code) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code IN ('alerts.view', 'alerts.manage')
WHERE r.role_name = 'administrator'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code IN ('alerts.view', 'alerts.manage')
WHERE r.role_name = 'security_analyst'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code = 'alerts.view'
WHERE r.role_name = 'team_lead'
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS network_alerts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('informational', 'low', 'medium', 'high')),
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'acknowledged', 'resolved')),
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    capture_source VARCHAR(20) NOT NULL CHECK (capture_source IN ('historical_import', 'live_capture')),
    capture_id VARCHAR(100),
    observed_count BIGINT NOT NULL,
    threshold_value BIGINT NOT NULL,
    window_seconds INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dedupe_key VARCHAR(255) NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_network_alerts_status
    ON network_alerts(status);
CREATE INDEX IF NOT EXISTS idx_network_alerts_severity
    ON network_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_network_alerts_rule
    ON network_alerts(rule_name);
CREATE INDEX IF NOT EXISTS idx_network_alerts_detected
    ON network_alerts(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_network_alerts_dedupe
    ON network_alerts(dedupe_key, detected_at DESC);

COMMIT;
