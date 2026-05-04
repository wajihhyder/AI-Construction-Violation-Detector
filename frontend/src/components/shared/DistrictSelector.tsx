import { Select } from '../ui/Select'

type Props = {
  districts: string[]
  value: string
  onChange: (v: string) => void
  label?: string
}

export function DistrictSelector({ districts, value, onChange, label }: Props) {
  const options = [
    { value: '', label: 'Select district...' },
    ...districts.map((d) => ({ value: d, label: d })),
  ]
  return (
    <Select
      label={label ?? 'District'}
      options={options}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
