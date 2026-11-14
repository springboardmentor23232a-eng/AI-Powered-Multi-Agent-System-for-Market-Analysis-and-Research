import { useState } from 'react'

export default function DataTable({ columns, rows, loading, empty = 'No records found', onRowClick }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-soc-border">
      <table className="min-w-full divide-y divide-soc-border text-sm">
        <thead className="bg-soc-panel2">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-soc-muted"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-soc-border bg-soc-panel">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-soc-muted font-mono">
                LOADING...
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-soc-muted">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={row.id ?? i}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`hover:bg-soc-panel2/60 ${onRowClick ? 'cursor-pointer' : ''}`}
              >
                {columns.map((c) => (
                  <td key={c.key} className="px-4 py-3 text-slate-300">
                    {c.render ? c.render(row) : row[c.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
