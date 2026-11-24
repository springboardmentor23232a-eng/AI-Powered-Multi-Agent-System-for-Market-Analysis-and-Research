-- NetShield AI - Module 3: Live packet capture foundation
-- Additive only. Existing historical packet records are preserved.

BEGIN;

ALTER TABLE public.network_packets
    ADD COLUMN IF NOT EXISTS capture_source VARCHAR(20) NOT NULL DEFAULT 'historical_import';

UPDATE public.network_packets
SET capture_source = 'historical_import'
WHERE capture_source IS NULL
   OR capture_id = 'legacy_packet_data_csv';

CREATE TABLE IF NOT EXISTS network_capture_sessions (
    id VARCHAR(64) PRIMARY KEY,
    interface_id VARCHAR(255) NOT NULL,
    interface_name VARCHAR(255),
    started_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'stopped', 'failed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    stopped_at TIMESTAMPTZ,
    packets_received BIGINT NOT NULL DEFAULT 0,
    packets_inserted BIGINT NOT NULL DEFAULT 0,
    packets_dropped BIGINT NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_network_packets_capture_source
    ON public.network_packets (capture_source);

CREATE INDEX IF NOT EXISTS idx_network_capture_sessions_status
    ON network_capture_sessions (status);

COMMIT;
