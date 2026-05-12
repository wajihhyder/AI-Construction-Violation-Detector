import { Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { pollReport } from '../../api/citizen'
import { CopyTrackingIdButton } from '../../components/shared/CopyTrackingIdButton'
import type { CitizenReportPoll } from '../../types/report'

type Props = {
  reportId: number
  trackingId: string
  onDone: (data: CitizenReportPoll) => void
}

const POLL_MS = 3000
const TIMEOUT_MS = 120000

export function ProcessingStep({ reportId, trackingId, onDone }: Props) {
  const [timedOut, setTimedOut] = useState(false)
  const onDoneRef = useRef(onDone)
  onDoneRef.current = onDone

  useEffect(() => {
    let cancelled = false
    const started = Date.now()

    const tick = async () => {
      if (cancelled) return
      try {
        const data = await pollReport(reportId)
        if (cancelled) return
        if (data.ai_result || data.status !== 'Processing') {
          cancelled = true
          onDoneRef.current(data)
          return
        }
        if (Date.now() - started > TIMEOUT_MS) {
          setTimedOut(true)
          return
        }
      } catch {
        if (!cancelled && Date.now() - started > TIMEOUT_MS) setTimedOut(true)
      }
    }

    tick()
    const id = window.setInterval(tick, POLL_MS)
    const timeoutId = window.setTimeout(() => {
      if (!cancelled) setTimedOut(true)
    }, TIMEOUT_MS)

    return () => {
      cancelled = true
      window.clearInterval(id)
      window.clearTimeout(timeoutId)
    }
  }, [reportId])

  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center gap-6 text-center">
      <Loader2 className="h-14 w-14 animate-spin text-white" />
      <div>
        <h2 className="text-xl font-medium">Analyzing your image…</h2>
        <p className="mt-3 text-sm text-[#888]">
          Your Tracking ID:{' '}
          <span className="font-mono tracking-wider text-white">{trackingId}</span>
        </p>
        <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
          <CopyTrackingIdButton trackingId={trackingId} />
        </div>
        <p className="mt-2 text-xs text-[#555]">
          Report #{String(reportId).padStart(5, '0')}
        </p>
      </div>
      {timedOut && (
        <div className="rounded-[var(--radius-md)] border border-white/30 bg-white/10 px-4 py-3 text-sm text-[#ccc]">
          Processing is taking longer than expected. Please try again later or contact SBCA.
        </div>
      )}
    </div>
  )
}
