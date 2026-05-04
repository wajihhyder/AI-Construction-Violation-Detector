import { useEffect, useState } from 'react'

import { fetchMapPins } from '../../api/authority'
import { MapView } from '../../components/shared/MapView'
import { Spinner } from '../../components/ui/Spinner'
import type { MapPin } from '../../types/report'

export function MapDashboard() {
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
            OpenStreetMap · every report with GPS (including pending AI). Gray = processing, yellow =
            under review, red = violation, green = cleared / no violation.
          </p>
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
