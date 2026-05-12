import type { AuthorityReportItem, MapPin, Stats } from '../types/report'
import { api } from './axios'

export async function fetchReports(params: {
  status?: string
  district?: string
  input_type?: string
  page?: number
  limit?: number
}) {
  const { data } = await api.get<{
    items: AuthorityReportItem[]
    total: number
    page: number
    limit: number
  }>('/api/authority/reports', { params })
  return data
}

export async function fetchReportDetail(reportId: number) {
  const { data } = await api.get(`/api/authority/reports/${reportId}`)
  return data
}

/**
 * Printable/downloadable screening report HTML.
 * Uses the shared axios client (same base URL + auth as other authority calls).
 */
export async function fetchReportNoticeHtml(reportId: number): Promise<string> {
  const { data } = await api.get<string>(`/api/authority/reports/${reportId}/notice`, {
    responseType: 'text',
    transformResponse: [(body) => body],
    headers: {
      Accept: 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
    },
  })
  if (typeof data !== 'string') {
    throw new Error('Unexpected report response')
  }
  return data
}

/** Trigger a browser download of the screening report as an HTML file (no pop-up). */
export function downloadReportNoticeHtml(reportId: number, html: string, trackingId?: string) {
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${trackingId?.trim() || `VS-REPORT-${String(reportId).padStart(5, '0')}`}.html`
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function patchReportStatus(
  reportId: number,
  body: { status: string; notes?: string | null },
) {
  const { data } = await api.patch(`/api/authority/reports/${reportId}/status`, body)
  return data
}

export async function fetchStats() {
  const { data } = await api.get<Stats>('/api/authority/reports/stats')
  return data
}

export async function fetchMapPins() {
  const { data } = await api.get<MapPin[]>('/api/authority/reports/map')
  return data
}

export async function fetchTimeline() {
  const { data } = await api.get<{ series: { date: string; count: number }[] }>(
    '/api/authority/reports/timeline',
  )
  return data
}
