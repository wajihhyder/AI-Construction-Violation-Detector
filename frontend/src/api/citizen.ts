import type { CitizenReportPoll } from '../types/report'
import { api } from './axios'

export async function fetchDistricts() {
  const { data } = await api.get<{ districts: string[] }>('/api/citizen/districts')
  return data.districts
}

export async function submitReport(form: FormData) {
  const { data } = await api.post<{
    report_id: number
    tracking_id: string
    status: string
    message: string
    gps_coords: string | null
    detected_district: string | null
  }>('/api/citizen/report', form)
  // Do not set Content-Type: browser/axios will add multipart boundary automatically.
  return data
}

export async function pollReport(reportId: number) {
  const { data } = await api.get<CitizenReportPoll>(`/api/citizen/report/${reportId}`)
  return data
}

export async function trackReport(trackingId: string) {
  const id = encodeURIComponent(trackingId.trim())
  const { data } = await api.get<CitizenReportPoll>(`/api/citizen/track/${id}`)
  return data
}

export async function patchDistrict(reportId: number, district_location: string) {
  const { data } = await api.patch(`/api/citizen/report/${reportId}/district`, {
    district_location,
  })
  return data
}

export type GeocodeResult = {
  district: string | null
  town: string | null
  label: string | null
  city?: string | null
  confidence?: string
  fallback?: boolean
  source?: string
  inside_karachi_bounds?: boolean
}

export async function reverseGeocode(lat: number, lng: number) {
  const { data } = await api.get<GeocodeResult>('/api/geocoding/reverse', {
    params: { lat, lng },
  })
  return data
}
