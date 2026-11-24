import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import api, { apiError } from '../api/client'
import { useAuth } from '../context/AuthContext'

const COLORS = ['#3b82f6', '#22d3ee', '#34d399', '#fbbf24', '#f87171', '#818cf8', '#94a3b8']

export default function TrafficMonitor() {
  const { hasPermission } = useAuth()
  const [summary, setSummary] = useState(null)
  const [protocols, setProtocols] = useState(null)
  const [ips, setIps] = useState(null)
  const [directions, setDirections] = useState(null)
  const [timeline, setTimeline] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    source_ip: '',
    destination_ip: '',
    ip_address: '',
    protocol: '',
    source_port: '',
    destination_port: '',
    port: '',
    capture_source: '',
  })
  const [packets, setPackets] = useState(null)
  const [packetPage, setPacketPage] = useState(1)
  const [downloadingReport, setDownloadingReport] = useState(false)
  const [downloadingCsv, setDownloadingCsv] = useState(false)
  const [success, setSuccess] = useState('')
  const [interfaces, setInterfaces] = useState([])
  const [selectedInterface, setSelectedInterface] = useState('')
  const [captureStatus, setCaptureStatus] = useState(null)
  const [captureBusy, setCaptureBusy] = useState(false)

  const canAnalyze = hasPermission('network.analyze')

  const loadCaptureControls = async () => {
    try {
      const [interfaceRes, statusRes] = await Promise.all([
        api.get('/network/interfaces'),
        api.get('/network/capture/status'),
      ])
      setInterfaces(interfaceRes.data.interfaces ?? [])
      setCaptureStatus(statusRes.data)
      if (!selectedInterface && interfaceRes.data.interfaces?.length) {
        setSelectedInterface(interfaceRes.data.interfaces[0].id)
      }
    } catch (err) {
      setError(apiError(err, 'Failed to load live capture information'))
    }
  }

  const startCapture = async () => {
    if (!selectedInterface) return
    setCaptureBusy(true)
    setError('')
    try {
      await api.post('/network/capture/start', null, {
        params: { interface_id: selectedInterface },
      })
      await loadCaptureControls()
    } catch (err) {
      setError(apiError(err, 'Failed to start packet capture'))
    } finally {
      setCaptureBusy(false)
    }
  }

  const stopCapture = async () => {
    setCaptureBusy(true)
    setError('')
    try {
      await api.post('/network/capture/stop', null, {
        params: captureStatus?.session?.id
          ? { session_id: captureStatus.session.id }
          : {},
      })
      await loadCaptureControls()
    } catch (err) {
      setError(apiError(err, 'Failed to stop packet capture'))
    } finally {
      setCaptureBusy(false)
    }
  }

  const load = async (signal, filterOverride = filters, pageOverride = packetPage) => {
    setError('')
    try {
      const params = new URLSearchParams()
      Object.entries(filterOverride).forEach(([key, value]) => {
        if (value) params.set(key, value)
      })
      params.set('page', String(pageOverride))
      params.set('page_size', '50')
      const [summaryRes, protocolRes, ipRes, directionRes, timelineRes, packetRes, alertRes] =
        await Promise.all([
          api.get('/network/summary', { signal }),
          api.get('/network/protocols', { signal }),
          api.get('/network/ips', { signal }),
          api.get('/network/directions', { signal }),
          api.get('/network/timeline?bucket=hour', { signal }),
          api.get(`/network/packets?${params.toString()}`, { signal }),
          api.get('/network/alerts', { signal }),
        ])
      setSummary(summaryRes.data)
      setProtocols(protocolRes.data)
      setIps(ipRes.data)
      setDirections(directionRes.data)
      setTimeline(timelineRes.data)
      setPackets(packetRes.data)
      setAlerts(alertRes.data)
    } catch (err) {
      if (err.code !== 'ERR_CANCELED') setError(apiError(err, 'Failed to load network traffic'))
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    load(controller.signal)
    loadCaptureControls()
    return () => controller.abort()
  }, [])

  const applyFilters = () => {
    setPacketPage(1)
    load(new AbortController().signal, filters, 1)
  }

  const clearFilters = () => {
    const cleared = {
      source_ip: '',
      destination_ip: '',
      ip_address: '',
      protocol: '',
      source_port: '',
      destination_port: '',
      port: '',
      capture_source: '',
    }
    setFilters(cleared)
    setPacketPage(1)
    load(new AbortController().signal, cleared, 1)
  }

  const changePacketPage = (nextPage) => {
    setPacketPage(nextPage)
    load(new AbortController().signal, filters, nextPage)
  }

  const downloadReport = async () => {
    setDownloadingReport(true)
    setError('')
    setSuccess('')
    try {
      const response = await api.get('/network/report', { responseType: 'blob' })
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = 'netshield-network-report.json'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(apiError(err, 'Failed to generate the network report'))
    } finally {
      setDownloadingReport(false)
    }
  }

  const downloadCsv = async () => {
    setDownloadingCsv(true)
    setError('')
    setSuccess('')
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value !== ''),
      )
      if (typeof window.showSaveFilePicker === 'function') {
        let fileHandle
        try {
          fileHandle = await window.showSaveFilePicker({
            suggestedName: 'netshield-network-packets.csv',
            types: [{ description: 'CSV file', accept: { 'text/csv': ['.csv'] } }],
          })
        } catch (pickerError) {
          if (pickerError.name === 'AbortError') return
          throw pickerError
        }
        const response = await api.get('/network/packets/export.csv', {
          params,
          adapter: 'fetch',
          responseType: 'stream',
        })
        const writable = await fileHandle.createWritable()
        await response.data.pipeTo(writable)
      } else {
        const response = await api.get('/network/packets/export.csv', {
          params,
          responseType: 'blob',
        })
        const url = window.URL.createObjectURL(response.data)
        const link = document.createElement('a')
        link.href = url
        link.download = 'netshield-network-packets.csv'
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      }
      setSuccess('CSV export downloaded. It includes all records matching the current filters.')
    } catch (err) {
      setError(apiError(err, 'Failed to export packet metadata as CSV'))
    } finally {
      setDownloadingCsv(false)
    }
  }

  const protocolChart = (protocols?.protocols ?? []).map((item) => ({
    name: item.protocol,
    value: item.packet_count,
    percentage: item.packet_percentage,
  }))

  const formatBytes = (bytes) =>
    bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(2)} MB` : `${(bytes / 1024).toFixed(2)} KB`

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-soc-text">Network Traffic Monitor</h1>
          <p className="text-sm text-soc-muted mt-1">
            Analysis of imported historical and live packet data
          </p>
        </div>
        {hasPermission('reports.generate') && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-ghost"
              onClick={downloadCsv}
              disabled={downloadingCsv}
            >
              <Download size={16} />
              {downloadingCsv ? 'Preparing CSV...' : 'Export Packet CSV'}
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={downloadReport}
              disabled={downloadingReport}
            >
              <Download size={16} />
              {downloadingReport ? 'Generating...' : 'Download JSON Report'}
            </button>
          </div>
        )}
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}
      {success && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-4 py-3 text-sm">{success}</div>}

      {canAnalyze && (
        <div className="card p-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-soc-text">Windows Live Capture</h2>
              <p className="mt-1 text-xs text-soc-muted">
                Metadata only · Requires Npcap · No packet payloads are stored
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="input min-w-64"
                value={selectedInterface}
                onChange={(event) => setSelectedInterface(event.target.value)}
                disabled={captureStatus?.active || captureBusy}
                aria-label="Network interface"
              >
                {interfaces.length ? interfaces.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                )) : <option value="">No interface discovered</option>}
              </select>
              {captureStatus?.active ? (
                <button type="button" className="btn-primary" onClick={stopCapture} disabled={captureBusy}>
                  Stop Capture
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={startCapture}
                  disabled={captureBusy || !selectedInterface}
                >
                  Start Capture
                </button>
              )}
            </div>
          </div>
          {captureStatus?.session && (
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-soc-muted sm:grid-cols-4">
              <span>Received: <b className="text-soc-text">{captureStatus.session.packets_received}</b></span>
              <span>Stored: <b className="text-soc-text">{captureStatus.session.packets_inserted}</b></span>
              <span>Dropped: <b className="text-soc-text">{captureStatus.session.packets_dropped}</b></span>
              <span>Status: <b className={captureStatus.active ? 'text-soc-green' : 'text-soc-warning'}>{captureStatus.active ? 'Running' : 'Stopped'}</b></span>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          ['Total Packets', summary?.total_packets?.toLocaleString()],
          ['Traffic Volume', formatBytes(summary?.total_bytes ?? 0)],
          ['Average Packet', summary?.average_packet_size ? `${summary.average_packet_size.toFixed(2)} bytes` : '0 bytes'],
          ['Unknown Direction', directions?.packet_counts?.unknown?.toLocaleString() ?? 'Unavailable'],
        ].map(([label, value]) => (
          <div key={label} className="card p-5">
            <div className="text-xs uppercase tracking-wider text-soc-muted">{label}</div>
            <div className="mt-2 text-xl font-bold font-mono text-soc-text">{value ?? 'Unavailable'}</div>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-soc-text mb-4">Packet Filters</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {[
            ['source_ip', 'Source IP'],
            ['destination_ip', 'Destination IP'],
            ['ip_address', 'Any IP'],
            ['protocol', 'Protocol'],
            ['source_port', 'Source port'],
            ['destination_port', 'Destination port'],
            ['port', 'Any port'],
          ].map(([field, label]) => (
            <input
              key={field}
              className="input"
              value={filters[field]}
              onChange={(event) => setFilters((current) => ({ ...current, [field]: event.target.value }))}
              placeholder={label}
              inputMode={field.includes('port') ? 'numeric' : 'text'}
            />
          ))}
          <select
            className="input"
            value={filters.capture_source}
            onChange={(event) => setFilters((current) => ({ ...current, capture_source: event.target.value }))}
            aria-label="Capture source"
          >
            <option value="">Combined (historical + live)</option>
            <option value="historical_import">Historical import</option>
            <option value="live_capture">Live capture</option>
          </select>
          <button type="button" className="btn-primary" onClick={applyFilters}>Apply Filters</button>
          <button type="button" className="btn-ghost" onClick={clearFilters}>Clear Filters</button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-soc-text mb-4">Protocol Distribution</h2>
          <div className="h-72">
            {protocolChart.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={protocolChart} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
                    {protocolChart.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="text-sm text-soc-muted text-center py-20">No protocol data available</div>}
          </div>
          <div className="space-y-2">
            {protocolChart.map((item, index) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-soc-muted"><span className="w-2 h-2 rounded-sm" style={{ background: COLORS[index % COLORS.length] }} />{item.name}</span>
                <span className="font-mono text-soc-text">{item.value.toLocaleString()} ({item.percentage}%)</span>
              </div>
            ))}
          </div>
        </div>

        <div className="xl:col-span-2 card p-5">
          <h2 className="text-sm font-semibold text-soc-text mb-4">Traffic Over Time</h2>
          <div className="h-72">
            {timeline?.items?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline.items}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2942" />
                  <XAxis dataKey="timestamp" stroke="#8b9bb8" fontSize={10} />
                  <YAxis stroke="#8b9bb8" fontSize={10} />
                  <Tooltip contentStyle={{ background: '#0d1424', border: '1px solid #1c2942', borderRadius: 10 }} />
                  <Area type="monotone" dataKey="packet_count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} name="Packets" />
                </AreaChart>
              </ResponsiveContainer>
            ) : <div className="text-sm text-soc-muted text-center py-20">No time-series packet data available</div>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {[
          ['Top Source IPs', ips?.source_ips],
          ['Top Destination IPs', ips?.destination_ips],
        ].map(([title, rows]) => (
          <div key={title} className="card p-5">
            <h2 className="text-sm font-semibold text-soc-text mb-4">{title}</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr><th className="th">IP address</th><th className="th">Packets</th><th className="th">Bytes</th></tr></thead>
                <tbody>
                  {(rows ?? []).slice(0, 10).map((row) => (
                    <tr key={row.ip} className="border-t border-soc-border"><td className="td font-mono">{row.ip}</td><td className="td font-mono">{row.packet_count}</td><td className="td font-mono">{formatBytes(row.traffic_bytes)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex items-center justify-between text-sm text-soc-muted">
              <span>Page {packetPage} of {Math.max(1, Math.ceil((packets?.total ?? 0) / 50))}</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={packetPage <= 1}
                  onClick={() => changePacketPage(packetPage - 1)}
                  className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2"
                >
                  Prev
                </button>
                <button
                  type="button"
                  disabled={packetPage >= Math.max(1, Math.ceil((packets?.total ?? 0) / 50))}
                  onClick={() => changePacketPage(packetPage + 1)}
                  className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-soc-text">Packet History</h2>
          <span className="text-xs text-soc-muted">{packets?.total?.toLocaleString() ?? 0} matching packets</span>
        </div>
        <p className="text-xs text-soc-muted mb-3">
          CSV exports include all matching records across pages and contain packet metadata only.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr><th className="th">Time</th><th className="th">Source</th><th className="th">Destination</th><th className="th">Protocol</th><th className="th">Size</th><th className="th">Direction</th></tr></thead>
            <tbody>
              {(packets?.items ?? []).map((packet) => (
                <tr key={packet.id} className="border-t border-soc-border">
                  <td className="td text-xs">{packet.packet_timestamp ? new Date(packet.packet_timestamp).toLocaleString() : 'Unknown'}</td>
                  <td className="td font-mono">{packet.source_ip ?? 'Unknown'}{packet.source_port ? `:${packet.source_port}` : ''}</td>
                  <td className="td font-mono">{packet.destination_ip ?? 'Unknown'}{packet.destination_port ? `:${packet.destination_port}` : ''}</td>
                  <td className="td"><span className="font-mono">{packet.protocol}</span>{packet.protocol_confidence === 'inferred' && <span className="text-soc-warning ml-2 text-xs">(inferred)</span>}</td>
                  <td className="td font-mono">{packet.packet_size ?? 0} bytes</td>
                  <td className="td">
                    <span className="capitalize">{packet.traffic_direction}</span>
                    <span className="ml-2 text-[10px] text-soc-muted">
                      {packet.capture_source === 'live_capture' ? 'LIVE' : 'HISTORICAL'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-soc-text mb-2">Detection Status</h2>
        <p className="text-sm text-soc-muted">
          {alerts?.total === 0
            ? 'No network alerts are stored. Deterministic detection rules are ready.'
            : `${alerts?.total ?? 0} stored network alert(s). Open the Network Alerts page for details.`}
        </p>
      </div>
    </div>
  )
}
