from fastapi import APIRouter, Depends, Query, Response, Request
from fastapi.responses import StreamingResponse
from typing import Literal
from .. import database
from ..dependencies import CurrentUser, get_db, require_permissions
from ..services import network_service, capture_service, detection_service

router = APIRouter(prefix="/network", tags=["network"])
VIEW = require_permissions("network.view")
ANALYZE = require_permissions("network.analyze")
REPORT = require_permissions("reports.generate")
ALERT_VIEW = require_permissions("alerts.view")
ALERT_MANAGE = require_permissions("alerts.manage")


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/interfaces")
def network_interfaces(
    user: CurrentUser = Depends(VIEW),
):
    return {"interfaces": capture_service.capture_manager.discover_interfaces()}


@router.post("/capture/start")
def start_capture(
    interface_id: str,
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return capture_service.capture_manager.start(conn, user, interface_id)


@router.post("/capture/stop")
def stop_capture(
    session_id: str | None = None,
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return capture_service.capture_manager.stop(conn, session_id)


@router.get("/capture/status")
def capture_status(
    user: CurrentUser = Depends(VIEW),
):
    return capture_service.capture_manager.get_status()


@router.get("/summary")
def network_summary(
    user: CurrentUser = Depends(VIEW),
    conn=Depends(get_db),
):
    return network_service.get_network_summary(conn)


@router.get("/protocols")
def protocols(
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return network_service.get_protocol_statistics(conn)


@router.get("/packets")
def packets(
    source_ip: str | None = Query(default=None, max_length=45),
    destination_ip: str | None = Query(default=None, max_length=45),
    ip_address: str | None = Query(default=None, max_length=45),
    protocol: str | None = Query(default=None, max_length=50),
    source_port: int | None = Query(default=None, ge=0, le=65535),
    destination_port: int | None = Query(default=None, ge=0, le=65535),
    port: int | None = Query(default=None, ge=0, le=65535),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    capture_source: Literal["historical_import", "live_capture"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return network_service.get_packets(
        conn, source_ip, destination_ip, ip_address, protocol,
        source_port, destination_port, port, start_time, end_time,
        page, page_size, capture_source,
    )


@router.get("/packets/export.csv")
def export_packets_csv(
    source_ip: str | None = Query(default=None, max_length=45),
    destination_ip: str | None = Query(default=None, max_length=45),
    ip_address: str | None = Query(default=None, max_length=45),
    protocol: str | None = Query(default=None, max_length=50),
    source_port: int | None = Query(default=None, ge=0, le=65535),
    destination_port: int | None = Query(default=None, ge=0, le=65535),
    port: int | None = Query(default=None, ge=0, le=65535),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    capture_source: Literal["historical_import", "live_capture", "combined"] = "combined",
    user: CurrentUser = Depends(REPORT),
):
    def stream():
        conn = database.get_connection()
        try:
            yield from network_service.iter_packet_csv(
                conn,
                source_ip,
                destination_ip,
                ip_address,
                protocol,
                source_port,
                destination_port,
                port,
                start_time,
                end_time,
                capture_source,
            )
        finally:
            database.put_connection(conn)

    return StreamingResponse(
        stream(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="netshield-network-packets.csv"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/ips")
def ip_statistics(
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return network_service.get_ip_statistics(conn)


@router.get("/directions")
def directions(
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return network_service.get_direction_statistics(conn)


@router.get("/timeline")
def timeline(
    bucket: Literal["minute", "hour", "day"] = "hour",
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    user: CurrentUser = Depends(ANALYZE),
    conn=Depends(get_db),
):
    return network_service.get_timeline(conn, bucket, start_time, end_time)


@router.get("/alerts")
def alerts(
    severity: Literal["informational", "low", "medium", "high"] | None = None,
    status: Literal["open", "acknowledged", "resolved"] | None = None,
    rule_name: str | None = Query(default=None, max_length=100),
    capture_source: Literal["historical_import", "live_capture"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    user: CurrentUser = Depends(ALERT_VIEW),
    conn=Depends(get_db),
):
    return detection_service.list_alerts(
        conn,
        severity,
        status,
        rule_name,
        capture_source,
        page,
        page_size,
    )


@router.get("/alerts/summary")
def alert_summary(
    user: CurrentUser = Depends(ALERT_VIEW),
    conn=Depends(get_db),
):
    return detection_service.get_summary(conn)


@router.post("/alerts/evaluate")
def evaluate_alerts(
    capture_source: Literal["historical_import", "live_capture"] = "live_capture",
    capture_id: str | None = None,
    user: CurrentUser = Depends(ALERT_MANAGE),
    conn=Depends(get_db),
):
    return detection_service.evaluate_packets(conn, capture_source, capture_id)


@router.get("/alerts/{alert_id}")
def alert_details(
    alert_id: int,
    user: CurrentUser = Depends(ALERT_VIEW),
    conn=Depends(get_db),
):
    return detection_service.get_alert(conn, alert_id)


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    request: Request,
    user: CurrentUser = Depends(ALERT_MANAGE),
    conn=Depends(get_db),
):
    return detection_service.acknowledge_alert(
        conn, alert_id, user, _client_ip(request)
    )


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    request: Request,
    user: CurrentUser = Depends(ALERT_MANAGE),
    conn=Depends(get_db),
):
    return detection_service.resolve_alert(
        conn, alert_id, user, _client_ip(request)
    )


@router.get("/system-status")
def system_status(
    user: CurrentUser = Depends(VIEW),
):
    return network_service.get_system_status()


@router.get("/report")
def report(
    user: CurrentUser = Depends(REPORT),
    conn=Depends(get_db),
):
    content = network_service.build_report(conn)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="netshield-network-report.json"'},
    )
