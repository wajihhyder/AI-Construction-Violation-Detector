/** Mirrors backend/services/rule_engine.py for citizen result UI only */
export const MAX_FLOORS_BY_DISTRICT: Record<string, number> = {
  Clifton: 4,
  Defence: 4,
  'Gulshan-e-Iqbal': 5,
  Korangi: 4,
  'Orangi Town': 3,
  Saddar: 6,
  Malir: 3,
  'North Nazimabad': 4,
  Landhi: 3,
  Baldia: 3,
}

export function maxFloorsForDistrict(district: string): number {
  return MAX_FLOORS_BY_DISTRICT[district] ?? 4
}
