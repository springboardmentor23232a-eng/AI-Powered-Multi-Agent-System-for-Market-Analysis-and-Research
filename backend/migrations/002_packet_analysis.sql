-- NetShield AI - Module 2: Additive packet-analysis metadata
-- This migration does not alter, truncate, or remove existing packet records.

BEGIN;

ALTER TABLE public.network_packets
    ADD COLUMN IF NOT EXISTS capture_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS frame_number BIGINT,
    ADD COLUMN IF NOT EXISTS protocol_confirmed BOOLEAN,
    ADD COLUMN IF NOT EXISTS protocol_confidence VARCHAR(20),
    ADD COLUMN IF NOT EXISTS traffic_direction VARCHAR(20) NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS import_key VARCHAR(64);

UPDATE public.network_packets
SET
    capture_id = COALESCE(capture_id, 'legacy_packet_data_csv'),
    protocol_confirmed = COALESCE(protocol_confirmed, FALSE),
    protocol_confidence = COALESCE(protocol_confidence, 'unknown'),
    traffic_direction = COALESCE(traffic_direction, 'unknown'),
    import_key = COALESCE(
        import_key,
        md5(
            'legacy_packet_data_csv|' ||
            COALESCE(id::TEXT, '') || '|' ||
            COALESCE(packet_timestamp::TEXT, '') || '|' ||
            COALESCE(source_ip, '') || '|' ||
            COALESCE(destination_ip, '') || '|' ||
            COALESCE(source_port::TEXT, '') || '|' ||
            COALESCE(destination_port::TEXT, '') || '|' ||
            COALESCE(protocol, '') || '|' ||
            COALESCE(packet_size::TEXT, '')
        )
    )
WHERE capture_id IS NULL
   OR protocol_confirmed IS NULL
   OR protocol_confidence IS NULL
   OR traffic_direction IS NULL
   OR import_key IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_network_packets_import_key
    ON public.network_packets(import_key);

CREATE INDEX IF NOT EXISTS idx_network_packets_timestamp
    ON public.network_packets(packet_timestamp);
CREATE INDEX IF NOT EXISTS idx_network_packets_source_ip
    ON public.network_packets(source_ip);
CREATE INDEX IF NOT EXISTS idx_network_packets_destination_ip
    ON public.network_packets(destination_ip);
CREATE INDEX IF NOT EXISTS idx_network_packets_protocol
    ON public.network_packets(protocol);
CREATE INDEX IF NOT EXISTS idx_network_packets_direction
    ON public.network_packets(traffic_direction);

COMMIT;
