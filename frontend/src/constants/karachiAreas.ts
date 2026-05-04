/**
 * Same towns + districts as `backend/core/districts.py` (keep in sync when editing backend).
 * Bundled in the client so the citizen flow does not wait on GET /api/citizen/districts.
 */
const ROWS: [string, string][] = [
  ['District Central', 'Gulberg'],
  ['District Central', 'Liaquatabad'],
  ['District Central', 'Nazimabad'],
  ['District Central', 'New Karachi'],
  ['District Central', 'New Nazimabad'],
  ['District East', 'Ferozabad'],
  ['District East', 'Gulshan-e-Iqbal'],
  ['District East', 'Gulzar-e-Hijri'],
  ['District East', 'Jamshed Quarters'],
  ['Karachi South', 'Arambagh'],
  ['Karachi South', 'Civil Lines'],
  ['Karachi South', 'Garden'],
  ['Karachi South', 'Lyari'],
  ['Karachi South', 'Saddar'],
  ['Karachi West', 'Mango Pir'],
  ['Karachi West', 'Mominabad'],
  ['Karachi West', 'Orangi Town'],
  ['Keamari', 'Baldia'],
  ['Keamari', 'Harbor'],
  ['Keamari', 'Maripur'],
  ['Keamari', 'SITE'],
  ['Korangi', 'Korangi'],
  ['Korangi', 'Landhi'],
  ['Korangi', 'Model Colony'],
  ['Korangi', 'Shah Faisal'],
  ['Malir', 'Airport'],
  ['Malir', 'Bin Qasim'],
  ['Malir', 'Gadap'],
  ['Malir', 'Ibrahim Hyderi'],
  ['Malir', 'Murad Memon'],
  ['Malir', 'Shah Mureed'],
]

function formatAreaLabel(district: string, town: string): string {
  return `${town} (${district})`
}

export const KARACHI_AREA_LABELS: string[] = [...new Set(ROWS.map(([d, t]) => formatAreaLabel(d, t)))].sort((a, b) =>
  a.localeCompare(b, undefined, { sensitivity: 'base' }),
)
