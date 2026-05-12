import L from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'

import type { MapPin } from '../../types/report'

function FitBounds({ pins }: { pins: MapPin[] }) {
  const map = useMap()
  if (pins.length === 0) return null
  if (pins.length === 1) {
    map.setView([pins[0].lat, pins[0].lng], 14)
    return null
  }
  const bounds = L.latLngBounds(pins.map((p) => [p.lat, p.lng] as [number, number]))
  map.fitBounds(bounds.pad(0.2))
  return null
}

type PinTone = {
  fill: string
  border: string
  glow: string
}

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ')
}

function pinTone(pin: MapPin): PinTone {
  if (pin.status === 'Verified') {
    return { fill: '#16a34a', border: '#dcfce7', glow: 'rgba(22, 163, 74, 0.35)' }
  }
  if (pin.violation_flag) {
    return { fill: '#dc2626', border: '#fecaca', glow: 'rgba(220, 38, 38, 0.35)' }
  }
  if (pin.status === 'Under_Review') {
    return { fill: '#f59e0b', border: '#fef3c7', glow: 'rgba(245, 158, 11, 0.35)' }
  }
  if (pin.status === 'Processing') {
    return { fill: '#8b5cf6', border: '#ede9fe', glow: 'rgba(139, 92, 246, 0.35)' }
  }
  if (pin.status === 'New') {
    return { fill: '#2563eb', border: '#dbeafe', glow: 'rgba(37, 99, 235, 0.35)' }
  }
  if (pin.status === 'Invalid' || pin.status === 'Closed_No_Violation') {
    return { fill: '#6b7280', border: '#e5e7eb', glow: 'rgba(107, 114, 128, 0.3)' }
  }
  return { fill: '#0f172a', border: '#e2e8f0', glow: 'rgba(15, 23, 42, 0.25)' }
}

type Props = {
  pins: MapPin[]
  height?: string
  filterViolationsOnly?: boolean
}

export function MapView({ pins, height = '420px', filterViolationsOnly }: Props) {
  const shown = filterViolationsOnly ? pins.filter((p) => p.violation_flag) : pins
  const center: [number, number] = [24.8607, 67.0011]

  return (
    <MapContainer
      center={center}
      zoom={11}
      style={{ height, width: '100%', borderRadius: 'var(--radius-lg)' }}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {shown.length > 0 && <FitBounds pins={shown} />}
      {shown.map((pin) => (
        <Marker
          key={pin.report_id}
          position={[pin.lat, pin.lng]}
          icon={(() => {
            const tone = pinTone(pin)
            return L.divIcon({
              className: '',
              html: `<div style="position:relative;width:18px;height:18px;border-radius:9999px;background:${tone.fill};border:3px solid ${tone.border};box-shadow:0 0 0 2px rgba(17,17,17,0.85),0 8px 18px ${tone.glow};"></div>`,
              iconSize: [18, 18],
              iconAnchor: [9, 9],
            })
          })()}
        >
          <Popup>
            <div className="text-xs">
              <div className="font-mono font-semibold">#{pin.report_id}</div>
              <div>{pin.district_location}</div>
              <div>{pin.violation_type ?? '—'}</div>
              <div>{formatStatus(pin.status)}</div>
              <a className="text-white underline" href={`/authority/reports/${pin.report_id}`}>
                View Report
              </a>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
