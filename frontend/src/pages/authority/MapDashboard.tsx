import { useEffect, useState } from 'react'

import { fetchMapPins } from '../../api/authority'
import { MapView } from '../../components/shared/MapView'
import { Spinner } from '../../components/ui/Spinner'
import { useAuthStore } from '../../store/authStore'
import type { MapPin } from '../../types/report'

export function MapDashboard() {
  const user = useAuthStore((s) => s.user)
  const [pins, setPins] = useState<MapPin[]>([])
  const [loading, setLoading] = useState(true)
  const [violationsOnly, setViolationsOnly] = useState(false)

  useEffect(() => {
    fetchMapPins()
      .then(setPins)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Map</h1>
          <p className="text-sm text-[#888]">
            OpenStreetMap · recorded violation workflows
            {user?.roleName === 'AUTHORITY' && user.assignedArea ? ` in ${user.assignedArea}` : ' across all visible areas'}
            . Verified reports are green and AI-flagged violations are red.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#bbb]">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#dc2626]" />
              Violation detected
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#16a34a]" />
              Verified
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#2563eb]" />
              New
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]" />
              Under review
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#8b5cf6]" />
              Processing
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#333] bg-[#111] px-3 py-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#6b7280]" />
              Invalid / closed
            </span>
          </div>
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-[#888]">
          <input
            type="checkbox"
            className="rounded border-[#333] bg-[#0a0a0a]"
            checked={violationsOnly}
            onChange={(e) => setViolationsOnly(e.target.checked)}
          />
          Show only violations
        </label>
      </div>
      <MapView pins={pins} height="560px" filterViolationsOnly={violationsOnly} />
    </div>
  )
}
