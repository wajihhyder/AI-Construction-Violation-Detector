import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { fetchReports, fetchStats, fetchTimeline } from '../../api/authority'
import { ReportCard } from '../../components/shared/ReportCard'
import { StatCard } from '../../components/shared/StatCard'
import { Select } from '../../components/ui/Select'
import { Skeleton } from '../../components/ui/Skeleton'
import type { AuthorityReportItem } from '../../types/report'
import { KARACHI_AREA_LABELS } from '../../constants/karachiAreas'

const COLORS = ['#ffffff', '#cccccc', '#888888', '#555555', '#333333', '#1a1a1a']

export function ReportsList() {
  const [items, setItems] = useState<AuthorityReportItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('All')
  const [districtFilter, setDistrictFilter] = useState('All')
  const [inputFilter, setInputFilter] = useState('All')
  const [stats, setStats] = useState<{
    total: number
    by_status: Record<string, number>
    compliant: number
    by_violation_type: Record<string, number>
  } | null>(null)
  const [timeline, setTimeline] = useState<{ date: string; count: number }[]>([])

  const limit = 20

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchReports({
      page,
      limit,
      status: statusFilter === 'All' ? undefined : statusFilter,
      district: districtFilter === 'All' ? undefined : districtFilter,
      input_type: inputFilter === 'All' ? undefined : inputFilter.toLowerCase(),
    })
      .then((r) => {
        if (!cancelled) {
          setItems(r.items)
          setTotal(r.total)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, statusFilter, districtFilter, inputFilter])

  useEffect(() => {
    fetchStats().then(setStats).catch(() => setStats(null))
    fetchTimeline()
      .then((t) => setTimeline(t.series))
      .catch(() => setTimeline([]))
  }, [])

  const pieData = stats
    ? Object.entries(stats.by_violation_type).map(([name, value]) => ({ name, value }))
    : []

  const totalPages = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="p-6 lg:p-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-sm text-[#888]">Overview and all violation reports</p>

      {stats && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Total reports" value={stats.total} accent="blue" />
          <StatCard
            title="New"
            value={stats.by_status['New'] ?? 0}
            accent="yellow"
          />
          <StatCard
            title="Verified"
            value={stats.by_status['Verified'] ?? 0}
            accent="green"
          />
          <StatCard title="Compliant (AI)" value={stats.compliant} accent="green" />
        </div>
      )}

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className="rounded-[var(--radius-lg)] border border-[#333] bg-[#111] p-4">
          <h2 className="mb-4 text-sm font-medium text-[#888]">Reports by violation type</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-[var(--radius-lg)] border border-[#333] bg-[#111] p-4">
          <h2 className="mb-4 text-sm font-medium text-[#888]">Submissions (30 days)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline}>
                <CartesianGrid stroke="#222" />
                <XAxis dataKey="date" tick={{ fill: '#555', fontSize: 10 }} />
                <YAxis tick={{ fill: '#555', fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#ffffff" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="mt-10 rounded-[var(--radius-lg)] border border-[#333] bg-[#111] p-4">
        <h2 className="mb-4 text-sm font-medium text-[#888]">Status distribution</h2>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={
                stats
                  ? Object.entries(stats.by_status).map(([name, value]) => ({ name, value }))
                  : []
              }
            >
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="name" tick={{ fill: '#888', fontSize: 11 }} />
              <YAxis tick={{ fill: '#888', fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#ffffff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-10 flex flex-wrap items-end gap-4">
        <div className="min-w-[160px]">
          <Select
            label="Status"
            options={[
              { value: 'All', label: 'All' },
              { value: 'New', label: 'New' },
              { value: 'Under_Review', label: 'Under Review' },
              { value: 'Verified', label: 'Verified' },
              { value: 'Invalid', label: 'Invalid' },
              { value: 'Processing', label: 'Processing' },
            ]}
            value={statusFilter}
            onChange={(e) => {
              setPage(1)
              setStatusFilter(e.target.value)
            }}
          />
        </div>
        <div className="min-w-[180px]">
          <Select
            label="District"
            options={[
              { value: 'All', label: 'All districts' },
              ...KARACHI_AREA_LABELS.map((d) => ({ value: d, label: d })),
            ]}
            value={districtFilter}
            onChange={(e) => {
              setPage(1)
              setDistrictFilter(e.target.value)
            }}
          />
        </div>
        <div className="min-w-[160px]">
          <Select
            label="Image type"
            options={[
              { value: 'All', label: 'All' },
              { value: 'Street', label: 'Street View' },
              { value: 'Aerial', label: 'Aerial' },
            ]}
            value={inputFilter}
            onChange={(e) => {
              setPage(1)
              setInputFilter(e.target.value)
            }}
          />
        </div>
      </div>

      <div className="mt-6 overflow-x-auto rounded-[var(--radius-lg)] border border-[#333]">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="border-b border-[#222] bg-[#0a0a0a] text-xs uppercase text-[#555]">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">District</th>
              <th className="px-3 py-2">Submitted</th>
              <th className="px-3 py-2">Reporter</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Violation</th>
              <th className="px-3 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={8} className="px-3 py-12 text-center text-[#555]">
                  <Skeleton className="mx-auto h-10 w-48" />
                </td>
              </tr>
            )}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-12 text-center text-[#555]">
                  No reports match your filters.
                </td>
              </tr>
            )}
            {!loading && items.map((r) => <ReportCard key={r.report_id} report={r} />)}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex justify-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            className="rounded border border-[#333] px-3 py-1 text-sm disabled:opacity-40"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm text-[#888]">
            Page {page} / {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            className="rounded border border-[#333] px-3 py-1 text-sm disabled:opacity-40"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
