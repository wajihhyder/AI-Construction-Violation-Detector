export type EncroachmentCategory =
  | 'road'
  | 'public_space'
  | 'water'
  | 'unmapped'
  | 'compliant'

export type EncroachmentBreakdown = Partial<Record<EncroachmentCategory, number>>

export type AIResult = {
  violation_flag: boolean
  violation_type: string | null
  detected_floors: number | null
  setback_error: number | null
  gps_coords: string
  image_evidence_path: string
  encroachment_total_m2?: number | null
  encroachment_breakdown?: EncroachmentBreakdown | null
}

export type CitizenReportPoll = {
  report_id: number
  tracking_id: string
  status: string
  district_location: string | null
  input_type: boolean | null
  submission_date: string | null
  reporter_type: string
  notes?: string | null
  ai_result: AIResult | null
}

/** Citizen-facing report record (alias for poll / track API shape). */
export type Report = CitizenReportPoll

export type AuthorityReportItem = {
  report_id: number
  submission_date: string
  district_location: string
  input_type: boolean | null
  reporter_type: string
  status: string
  violation_type: string | null
  violation_flag: boolean | null
}

export type Stats = {
  total: number
  by_status: Record<string, number>
  by_violation_type: Record<string, number>
  compliant: number
}

export type MapPin = {
  report_id: number
  lat: number
  lng: number
  district_location: string
  status: string
  violation_flag: boolean | null
  violation_type: string | null
}
