import { useEffect, useMemo, useState } from 'react'
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
  Rectangle,
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
import { useAuthStore } from '../../store/authStore'
import type { AuthorityReportItem } from '../../types/report'
import { KARACHI_AREA_LABELS } from '../../constants/karachiAreas'

const VIOLATION_COLORS = ['#ffffff', '#d4d4d8', '#a1a1aa', '#71717a', '#52525b', '#3f3f46']
const STATUS_COLORS: Record<string, string> = {
  New: '#ffffff',
  Under_Review: '#d4d4d8',
  Verified: '#a1a1aa',
  Invalid: '#71717a',
  Processing: '#52525b',
}

function formatChartLabel(value: string) {
  return value.replace(/_/g, ' ')
}

function formatShortDate(value: string) {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function EmptyChartState({ message }: { message: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-[#333] bg-[#0a0a0a] text-sm text-[#888]">
      {message}
    </div>
  )
}

type ActiveStatusBarProps = {
  fill?: string
  x?: number
  y?: number
  width?: number
  height?: number
}

function ActiveStatusBar({
  fill = '#ffffff',
  x = 0,
  y = 0,
  width = 0,
  height = 0,
}: ActiveStatusBarProps) {
  if (width <= 0 || height <= 0) return null

  return (
    <Rectangle
      x={x - 2}
      y={y - 6}
      width={width + 4}
      height={height + 6}
      fill={fill}
      radius={[10, 10, 0, 0]}
    />
  )
}

export function ReportsList() {
  const user = useAuthStore((s) => s.user)
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
  const scopedArea = user?.roleName === 'AUTHORITY' ? user.assignedArea : null
  const districtOptions = useMemo(
    () => (scopedArea ? [scopedArea] : KARACHI_AREA_LABELS),
    [scopedArea],
  )

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
    Promise.all([fetchStats(), fetchTimeline()])
      .then(([statsData, timelineData]) => {
        setStats(statsData)
        setTimeline(timelineData.series)
      })
      .catch(() => {
        setStats(null)
        setTimeline([])
      })
  }, [])

  const pieData = useMemo(
    () =>
      stats
        ? Object.entries(stats.by_violation_type)
            .map(([name, value]) => ({ name, value }))
            .filter((entry) => entry.value > 0)
            .sort((a, b) => b.value - a.value)
        : [],
    [stats],
  )
  const statusData = useMemo(
    () =>
      stats
        ? Object.entries(stats.by_status)
            .map(([name, value]) => ({ name, value }))
            .filter((entry) => entry.value > 0)
            .sort((a, b) => b.value - a.value)
        : [],
    [stats],
  )
  const totalViolationReports = pieData.reduce((sum, entry) => sum + entry.value, 0)
  const chartCardClass =
    'rounded-[var(--radius-lg)] border border-[#333] bg-[#111] p-5'

  const totalPages = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="p-6 lg:p-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-sm text-[#888]">
        {scopedArea
          ? `Violation reports for your assigned area: ${scopedArea}`
          : 'Overview of recorded violation reports'}
      </p>

      {stats && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Total reports" value={stats.total} accent="blue" />
          <StatCard
            title="New"
            value={stats.by_status['New'] ?? 0}
            accent="yellow"
          />
          <StatCard
            title="Under Review"
            value={stats.by_status['Under_Review'] ?? 0}
            accent="yellow"
          />
          <StatCard title="Verified" value={stats.by_status['Verified'] ?? 0} accent="green" />
        </div>
      )}

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className={chartCardClass}>
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Reports by violation type</h2>
              <p className="mt-1 text-xs text-[#888]">Breakdown of detected case categories</p>
            </div>
            <span className="rounded-full border border-[#333] bg-[#0a0a0a] px-3 py-1 text-xs font-medium text-white">
              {totalViolationReports} total
            </span>
          </div>
          <div className="h-72">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="48%"
                    innerRadius={58}
                    outerRadius={92}
                    paddingAngle={3}
                    labelLine={false}
                    stroke="#111111"
                    strokeWidth={3}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={entry.name} fill={VIOLATION_COLORS[i % VIOLATION_COLORS.length]} />
                    ))}
                  </Pie>
                  <text
                    x="50%"
                    y="44%"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#888888"
                    className="text-[13px] font-medium"
                  >
                    Violation mix
                  </text>
                  <text
                    x="50%"
                    y="53%"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#ffffff"
                    className="text-[26px] font-semibold"
                  >
                    {totalViolationReports}
                  </text>
                  <Tooltip
                    formatter={(value, name) => [`${value} reports`, formatChartLabel(String(name))]}
                    contentStyle={{
                      borderRadius: 14,
                      border: '1px solid #333333',
                      backgroundColor: '#111111',
                      color: '#ffffff',
                    }}
                    itemStyle={{ color: '#ffffff' }}
                    labelStyle={{ color: '#888888' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    formatter={(value) => formatChartLabel(String(value))}
                    wrapperStyle={{ color: '#dddddd', fontSize: '12px', paddingTop: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartState message="No violations recorded yet." />
            )}
          </div>
        </div>
        <div className={chartCardClass}>
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-white">Submissions (30 days)</h2>
            <p className="mt-1 text-xs text-[#888]">Daily report volume for the past month</p>
          </div>
          <div className="h-72">
            {timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeline.map((entry) => ({ ...entry, label: formatShortDate(entry.date) }))}
                  margin={{ top: 12, right: 10, left: -18, bottom: 4 }}
                >
                  <CartesianGrid stroke="#222222" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fill: '#888888', fontSize: 11 }}
                    tickLine={false}
                    axisLine={{ stroke: '#333333' }}
                    minTickGap={24}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fill: '#888888', fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    formatter={(value) => [`${value} submissions`, 'Reports']}
                    contentStyle={{
                      borderRadius: 14,
                      border: '1px solid #333333',
                      backgroundColor: '#111111',
                      color: '#ffffff',
                    }}
                    itemStyle={{ color: '#ffffff' }}
                    labelStyle={{ color: '#888888' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#ffffff"
                    strokeWidth={3}
                    dot={{ r: 3, strokeWidth: 2, stroke: '#ffffff', fill: '#111111' }}
                    activeDot={{ r: 5, strokeWidth: 0, fill: '#ffffff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChartState message="No submissions in the selected time range." />
            )}
          </div>
        </div>
      </div>

      <div className={`mt-10 ${chartCardClass}`}>
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-white">Status distribution</h2>
          <p className="mt-1 text-xs text-[#888]">Current workflow stage of reported cases</p>
        </div>
        <div className="h-64">
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="#222222" vertical={false} />
                <XAxis
                  dataKey="name"
                  tickFormatter={formatChartLabel}
                  tick={{ fill: '#888888', fontSize: 11 }}
                  tickLine={false}
                  axisLine={{ stroke: '#333333' }}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fill: '#888888', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(value, name) => [`${value} reports`, formatChartLabel(String(name))]}
                  labelFormatter={(label) => formatChartLabel(String(label))}
                  cursor={false}
                  contentStyle={{
                    borderRadius: 14,
                    border: '1px solid #333333',
                    backgroundColor: '#111111',
                    color: '#ffffff',
                  }}
                  itemStyle={{ color: '#ffffff' }}
                  labelStyle={{ color: '#888888' }}
                />
                <Bar
                  dataKey="value"
                  radius={[10, 10, 0, 0]}
                  maxBarSize={72}
                  activeBar={(props) => <ActiveStatusBar {...props} />}
                >
                  {statusData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={STATUS_COLORS[entry.name] ?? VIOLATION_COLORS[0]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState message="No status data available yet." />
          )}
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
        {!scopedArea && (
          <div className="min-w-[180px]">
            <Select
              label="District"
              options={[
                { value: 'All', label: 'All districts' },
                ...districtOptions.map((d) => ({ value: d, label: d })),
              ]}
              value={districtFilter}
              onChange={(e) => {
                setPage(1)
                setDistrictFilter(e.target.value)
              }}
            />
          </div>
        )}
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
