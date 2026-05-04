import { format } from 'date-fns'
import { Bookmark } from 'lucide-react'

import type { CitizenReportPoll } from '../../types/report'
import { maxFloorsForDistrict } from '../../constants/sbca'
import { CopyTrackingIdButton } from '../../components/shared/CopyTrackingIdButton'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { ViolationBadge } from '../../components/shared/ViolationBadge'

type Props = {
  data: CitizenReportPoll
  onReset: () => void
}

export function ResultStep({ data, onReset }: Props) {
  const ai = data.ai_result
  const district = data.district_location ?? ''
  const violation = ai?.violation_flag
  const imgSrc = ai?.image_evidence_path ?? ''

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-g-blue/40 bg-g-blue/10 p-4">
        <div className="flex items-start gap-3">
          <Bookmark className="mt-0.5 shrink-0 text-g-blue" size={22} aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-white">Your Tracking ID</p>
            <p className="mt-2 break-all font-mono text-2xl font-semibold tracking-wider text-white">
              {data.tracking_id}
            </p>
            <div className="mt-3">
              <CopyTrackingIdButton trackingId={data.tracking_id} />
            </div>
            <p className="mt-3 text-xs text-[#888]">
              Save this ID to track your complaint later.
            </p>
          </div>
        </div>
      </div>

      {violation ? (
        <div className="rounded-[var(--radius-lg)] border-2 border-white bg-black px-6 py-4 text-center font-semibold text-white">
          VIOLATION DETECTED
          <div className="mt-2 flex justify-center">
            <ViolationBadge type={ai?.violation_type ?? null} />
          </div>
        </div>
      ) : (
        <div className="rounded-[var(--radius-lg)] border border-[#333] bg-white px-6 py-4 text-center font-semibold text-black">
          NO VIOLATION FOUND
        </div>
      )}

      {ai?.violation_type === 'Extra_Floor' && ai.detected_floors != null && (
        <p className="text-sm text-[#888]">
          Detected {ai.detected_floors} floors — Max allowed:{' '}
          {maxFloorsForDistrict(district)} floors in {district}
        </p>
      )}
      {ai?.violation_type === 'Setback_Breach' && ai.setback_error != null && (
        <p className="text-sm text-[#888]">
          Setback deviation: {ai.setback_error} meters below required minimum
        </p>
      )}

      {imgSrc && (
        <img
          src={imgSrc}
          alt="Evidence"
          className="max-h-80 rounded-[var(--radius-lg)] border border-[#333]"
        />
      )}

      <div className="grid gap-2 text-sm">
        <div>
          <span className="text-[#555]">Tracking ID</span>{' '}
          <span className="font-mono text-white">{data.tracking_id}</span>
        </div>
        <div>
          <span className="text-[#555]">Report ID</span>{' '}
          <span className="font-mono text-white">#{String(data.report_id).padStart(5, '0')}</span>
        </div>
        <div>
          <span className="text-[#555]">District</span>{' '}
          <span>{district}</span>
        </div>
        <div>
          <span className="text-[#555]">GPS</span>{' '}
          <span className="font-mono text-xs text-[#888]">{ai?.gps_coords}</span>
        </div>
        {data.submission_date && (
          <div>
            <span className="text-[#555]">Submitted</span>{' '}
            <span>{format(new Date(data.submission_date), 'PPpp')}</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <span className="text-[#555]">Status</span>
          <Badge status={data.status}>{data.status}</Badge>
        </div>
      </div>

      <Button onClick={onReset}>Submit Another Report</Button>
    </div>
  )
}
