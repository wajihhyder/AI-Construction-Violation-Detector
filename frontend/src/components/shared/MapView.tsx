import L from 'leaflet'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'

import type { MapPin } from '../../types/report'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: string })._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, shadowUrl: markerShadow })

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

function pinColor(pin: MapPin): string {
  if (pin.status === 'Under_Review') return '#cccccc'
  if (pin.status === 'Processing') return '#888888'
  if (pin.violation_flag) return '#ffffff'
  return '#666666'
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
          icon={L.divIcon({
            className: '',
            html: `<div style="width:14px;height:14px;border-radius:50%;background:${pinColor(
              pin,
            )};border:2px solid #111;box-shadow:0 0 0 1px #333"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
          })}
        >
          <Popup>
            <div className="text-xs">
              <div className="font-mono font-semibold">#{pin.report_id}</div>
              <div>{pin.district_location}</div>
              <div>{pin.violation_type ?? '—'}</div>
              <div>{pin.status}</div>
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
