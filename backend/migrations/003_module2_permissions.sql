-- NetShield AI - Module 2: additive network/report permissions
-- Existing role mappings and records are preserved.

BEGIN;

INSERT INTO permissions (permission_code, module, description) VALUES
    ('network.view', 'network', 'View captured network traffic and traffic statistics'),
    ('network.analyze', 'network', 'Analyze packets, protocols, IP activity and time-series traffic'),
    ('reports.generate', 'reports', 'Generate permitted network and security reports')
ON CONFLICT (permission_code) DO NOTHING;

-- Administrators retain full platform access, including the additive Module 2 permissions.
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code IN ('network.view', 'network.analyze', 'reports.generate')
WHERE r.role_name = 'administrator'
ON CONFLICT DO NOTHING;

-- Security analysts may monitor, analyze and generate permitted reports.
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code IN ('network.view', 'network.analyze', 'reports.generate')
WHERE r.role_name = 'security_analyst'
ON CONFLICT DO NOTHING;

-- Team leads may monitor relevant traffic and generate permitted reports.
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.permission_code IN ('network.view', 'reports.generate')
WHERE r.role_name = 'team_lead'
ON CONFLICT DO NOTHING;

COMMIT;
