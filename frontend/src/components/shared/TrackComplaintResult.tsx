import { format } from 'date-fns'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'

import type { CitizenReportPoll } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

type Props = {
  data: CitizenReportPoll
  onClose: () => void
  onRefresh?: () => void | Promise<void>
  refreshing?: boolean
}

export function TrackComplaintResult({ data, onClose, onRefresh, refreshing }: Props) {
  const ai = data.ai_result
  const submitted =
    data.submission_date != null ? format(new Date(data.submission_date), 'PPP') : '—'
  const inputLabel =
    data.input_type === null ? '—' : data.input_type ? 'Street View' : 'Aerial'

  const processing = data.status === 'Processing'
  const manualReview = data.status === 'Under_Review' || ai?.violation_type === 'Manual_Review'
  const invalid = data.status === 'Invalid'

  let aiSummary: ReactNode
  if (processing) {
    aiSummary = (
      <div className="mt-3 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-sm text-[#888]">
          <div
            className="h-5 w-5 animate-spin rounded-full border-2 border-[#333] border-t-g-blue"
            aria-hidden
          />
          AI analysis in progress…
        </div>
        {onRefresh && (
          <Button type="button" variant="secondary" disabled={refreshing} onClick={() => void onRefresh()}>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </Button>
        )}
      </div>
    )
  } else if (invalid) {
    aiSummary = (
      <p className="mt-2 text-sm font-medium text-[#ddd]">
        Automated analysis could not be completed.
        {data.notes ? ` ${data.notes}` : ''}
      </p>
    )
  } else if (manualReview) {
    aiSummary = (
      <p className="mt-2 text-sm font-medium text-[#ddd]">
        Submitted for manual review.
        {data.notes ? ` ${data.notes}` : ''}
      </p>
    )
  } else if (!ai) {
    aiSummary = (
      <p className="mt-2 text-sm text-[#888]">
        AI result not available yet.
        {data.notes ? ` ${data.notes}` : ''}
      </p>
    )
  } else if (ai.violation_flag) {
    const label = ai.violation_type?.replace(/_/g, ' ') ?? 'Violation'
    aiSummary = (
      <p className="mt-2 text-sm font-medium text-g-red">
        AI Result: VIOLATION DETECTED — {label}
      </p>
    )
  } else {
    aiSummary = (
      <p className="mt-2 text-sm font-medium text-g-green">
        AI Result: NO VIOLATION FOUND
        {data.notes ? ` ${data.notes}` : ''}
      </p>
    )
  }

  return (
    <div className="relative rounded-[var(--radius-lg)] border border-[#333] bg-[#111] p-4">
      <button
        type="button"
        aria-label="Close"
        className="absolute right-3 top-3 text-[#888] hover:text-white"
        onClick={onClose}
      >
        <X size={18} />
      </button>

      <div className="pr-8">
        <div className="font-mono text-sm font-semibold text-white">Report: {data.tracking_id}</div>
        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-[#888]">
          <span>District: {data.district_location ?? '—'}</span>
          <span>Submitted: {submitted}</span>
        </div>
        <div className="mt-1 text-sm text-[#888]">
          Type: <span className="text-white">{inputLabel}</span>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-sm text-[#555]">Status:</span>
          <Badge status={data.status}>{data.status.replace(/_/g, ' ')}</Badge>
        </div>

        {aiSummary}
      </div>
    </div>
  )
}
