import { useEffect, useState } from 'react'

import { reverseGeocode } from '../../api/citizen'
import { KARACHI_AREA_LABELS } from '../../constants/karachiAreas'
import { DistrictSelector } from '../../components/shared/DistrictSelector'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'

type Props = {
  /** Optional override; defaults to bundled list for zero latency */
  districts?: string[]
  gps: { lat: number; lng: number } | null
  onSubmitReport: (district: string) => Promise<void>
}

export function DistrictStep({ districts = KARACHI_AREA_LABELS, gps, onSubmitReport }: Props) {
  const [detected, setDetected] = useState<string | null>(null)
  const [geoSource, setGeoSource] = useState<string | null>(null)
  const [loadingGeo, setLoadingGeo] = useState(false)
  const [selected, setSelected] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Single GPS lookup when coordinates change — not tied to district list loading.
  useEffect(() => {
    if (!gps) {
      setDetected(null)
      setGeoSource(null)
      setLoadingGeo(false)
      return
    }
    let cancelled = false
    setLoadingGeo(true)
    setDetected(null)
    reverseGeocode(gps.lat, gps.lng)
      .then((res) => {
        if (cancelled) return
        setGeoSource(res.source ?? null)
        const label = res.label?.trim() || res.district?.trim() || null
        setDetected(label)
        if (label && KARACHI_AREA_LABELS.includes(label)) {
          setSelected(label)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDetected(null)
          setGeoSource(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingGeo(false)
      })
    return () => {
      cancelled = true
    }
  }, [gps])

  async function confirmDistrict(district: string) {
    setSubmitting(true)
    try {
      await onSubmitReport(district)
    } finally {
      setSubmitting(false)
    }
  }

  const suggestionMatchesList = Boolean(detected && KARACHI_AREA_LABELS.includes(detected))

  return (
    <div className="space-y-6">
      <div className="rounded-[var(--radius-md)] border border-[#333] bg-[#111] p-4">
        <div className="text-xs text-[#555]">Coordinates</div>
        {gps ? (
          <p className="mt-1 font-mono text-sm text-white">
            {gps.lat.toFixed(6)}, {gps.lng.toFixed(6)}
          </p>
        ) : (
          <p className="mt-1 font-mono text-sm text-[#888]">No GPS detected</p>
        )}
      </div>

      {gps && loadingGeo && (
        <div className="flex items-center gap-2 text-sm text-[#888]">
          <Spinner className="!h-5 !w-5 shrink-0" /> Matching GPS to Karachi district and town…
        </div>
      )}

      {gps && !loadingGeo && detected && suggestionMatchesList && (
        <p className="text-sm text-[#aaa]">
          <span className="text-[#888]">GPS suggests: </span>
          <span className="font-medium text-white">{detected}</span>
          {geoSource === 'karachi_admin' && (
            <span className="ml-2 text-xs text-[#555]">(admin map)</span>
          )}
          {geoSource === 'geoapify' && (
            <span className="ml-2 text-xs text-[#555]">(reverse geocode)</span>
          )}
        </p>
      )}

      {gps && !loadingGeo && detected && !suggestionMatchesList && (
        <p className="text-sm text-[#888]">
          GPS hint “{detected}” is not in the official town list — pick the correct area below.
        </p>
      )}

      <div className="space-y-4">
        <DistrictSelector
          districts={districts}
          value={selected}
          onChange={setSelected}
          label="Town (district)"
        />
        <Button
          disabled={!selected || submitting}
          onClick={() => confirmDistrict(selected)}
        >
          Submit Report
        </Button>
      </div>
    </div>
  )
}
