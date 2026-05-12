import { format } from 'date-fns'
import { ArrowLeft, MapPin } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate, useParams } from 'react-router-dom'

import {
  downloadReportNoticeHtml,
  fetchReportDetail,
  fetchReportNoticeHtml,
  patchReportStatus,
} from '../../api/authority'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Modal } from '../../components/ui/Modal'
import { ViolationBadge } from '../../components/shared/ViolationBadge'
import { Spinner } from '../../components/ui/Spinner'

type Detail = {
  report_id: number
  tracking_id: string
  submission_date: string
  district_location: string
  input_type: boolean | null
  reporter_type: string
  status: string
  notes: string | null
  ai_result: {
    violation_flag: boolean
    violation_type: string | null
    detected_floors: number | null
    setback_error: number | null
    gps_coords: string
    image_evidence_path: string
  } | null
}

export function ReportDetail() {
  const { reportId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<Detail | null>(null)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState('')
  const [lightbox, setLightbox] = useState(false)

  const id = Number(reportId)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchReportDetail(id)
      .then((d) => {
        setData(d as Detail)
        setNotes((d as Detail).notes ?? '')
      })
      .catch(() => navigate('/authority/reports'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  if (loading || !data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner />
      </div>
    )
  }

  const mapsUrl = `https://www.google.com/maps?q=${encodeURIComponent(data.ai_result?.gps_coords ?? '')}`

  async function updateStatus(next: string) {
    try {
      await patchReportStatus(data.report_id, { status: next, notes: notes || null })
      toast.success('Status updated')
      const d = await fetchReportDetail(data.report_id)
      setData(d as Detail)
    } catch {
      /* axios interceptor */
    }
  }

  async function openPrintableNotice() {
    try {
      const html = await fetchReportNoticeHtml(data.report_id)
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const w = window.open(url, '_blank', 'noopener,noreferrer')
      if (!w) {
        URL.revokeObjectURL(url)
        toast.error('Pop-up blocked — use Download notice or allow pop-ups for this site')
        return
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 600_000)
      w.focus?.()
    } catch {
      /* fetchReportNoticeHtml toasts API failures */
    }
  }

  async function downloadNotice() {
    try {
      const html = await fetchReportNoticeHtml(data.report_id)
      downloadReportNoticeHtml(data.report_id, html, data.tracking_id)
      toast.success('Report downloaded')
    } catch {
      /* fetchReportNoticeHtml toasts API failures */
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <button
        type="button"
        className="mb-6 flex items-center gap-2 text-sm text-[#888] hover:text-white"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft size={18} /> Back
      </button>

      <div className="grid gap-8 lg:grid-cols-2">
        <Card className="overflow-hidden p-0">
          <button type="button" className="relative block w-full" onClick={() => setLightbox(true)}>
            <img
              src={data.ai_result?.image_evidence_path ?? ''}
              alt="Evidence"
              className="max-h-[480px] w-full object-contain"
            />
          </button>
        </Card>

        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="font-mono text-2xl font-semibold">
                #{String(data.report_id).padStart(5, '0')}
              </h1>
              <p className="mt-1 text-sm text-[#888]">
                {format(new Date(data.submission_date), 'PPpp')}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" className="!text-xs" onClick={() => void openPrintableNotice()}>
                Printable report
              </Button>
              <Button variant="secondary" className="!text-xs" onClick={() => void downloadNotice()}>
                Download report
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <MapPin size={16} className="text-white" />
            <span>{data.district_location}</span>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge>{data.reporter_type}</Badge>
            <Badge>
              {data.input_type === null ? 'Unknown' : data.input_type ? 'Street View' : 'Aerial'}
            </Badge>
            <Badge status={data.status}>{data.status.replace('_', ' ')}</Badge>
          </div>

          <div>
            <span className="text-xs text-[#555]">GPS</span>
            <a
              href={mapsUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-1 block font-mono text-sm text-white hover:underline"
            >
              {data.ai_result?.gps_coords}
            </a>
          </div>

          <Card className="p-4">
            <h2 className="text-sm font-medium text-[#888]">AI analysis</h2>
            {data.ai_result?.violation_type === 'Manual_Review' ? (
              <div className="mt-3 rounded-md border border-[#666] bg-[#2a2a2a] px-3 py-2 text-[#e0e0e0]">
                Manual review required
              </div>
            ) : data.ai_result?.violation_flag ? (
              <div className="mt-3 rounded-md border border-white/25 bg-white/10 px-3 py-2 text-white">
                Violation flagged
              </div>
            ) : (
              <div className="mt-3 rounded-md border border-[#666] bg-[#2a2a2a] px-3 py-2 text-[#e0e0e0]">
                No violation flagged
              </div>
            )}
            <div className="mt-3">
              <ViolationBadge type={data.ai_result?.violation_type ?? null} />
            </div>
            {data.ai_result?.detected_floors != null && (
              <p className="mt-2 text-sm text-[#888]">
                Detected floors: {data.ai_result.detected_floors}
              </p>
            )}
            {data.ai_result?.setback_error != null && (
              <p className="mt-2 text-sm text-[#888]">
                Setback error (m): {data.ai_result.setback_error}
              </p>
            )}
          </Card>

          <Card className="space-y-4 p-4">
            <h2 className="text-sm font-medium text-[#888]">Authority action</h2>
            <label className="block w-full text-sm text-[#888]">
              Notes
              <textarea
                className="mt-1 w-full rounded-[var(--radius-md)] border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-white"
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {data.status === 'New' && (
                <Button variant="warning" onClick={() => updateStatus('Under_Review')}>
                  Move to Under Review
                </Button>
              )}
              {data.status === 'Under_Review' && (
                <>
                  <Button onClick={() => updateStatus('Verified')}>Mark Verified</Button>
                  <Button variant="danger" onClick={() => updateStatus('Invalid')}>
                    Mark Invalid
                  </Button>
                </>
              )}
            </div>
          </Card>
        </div>
      </div>

      <Modal open={lightbox} onClose={() => setLightbox(false)} title="Evidence">
        <img
          src={data.ai_result?.image_evidence_path ?? ''}
          alt="Full"
          className="max-h-[80vh] w-full object-contain"
        />
      </Modal>
    </div>
  )
}
