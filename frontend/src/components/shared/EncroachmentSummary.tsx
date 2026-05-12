import type { EncroachmentBreakdown, EncroachmentCategory } from '../../types/report'

const CATEGORY_ORDER: EncroachmentCategory[] = [
  'road',
  'public_space',
  'water',
  'unmapped',
  'compliant',
]

const CATEGORY_LABEL: Record<EncroachmentCategory, string> = {
  road: 'Road encroachment',
  public_space: 'Public-space encroachment',
  water: 'Water encroachment',
  unmapped: 'Unmapped construction',
  compliant: 'Compliant footprint',
}

const CATEGORY_SWATCH: Record<EncroachmentCategory, string> = {
  road: 'bg-[#ff3c5f]',
  public_space: 'bg-[#c850dc]',
  water: 'bg-[#50aaff]',
  unmapped: 'bg-[#ffaf46]',
  compliant: 'bg-[#46c878]',
}

function formatArea(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return '0.0 m²'
  return `${value.toFixed(1)} m²`
}

export function EncroachmentSummary({
  total,
  breakdown,
}: {
  total?: number | null
  breakdown?: EncroachmentBreakdown | null
}) {
  if (breakdown == null) return null

  return (
    <div className="rounded-[var(--radius-md)] border border-[#333] bg-[#0a0a0a] p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-medium text-white">Encroachment classification</h3>
        <span className="text-xs text-[#888]">Total: {formatArea(total)}</span>
      </div>
      <ul className="mt-3 space-y-2">
        {CATEGORY_ORDER.map((cat) => (
          <li key={cat} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2">
              <span className={`inline-block h-3 w-3 rounded-sm ${CATEGORY_SWATCH[cat]}`} aria-hidden />
              <span className="text-[#cfcfcf]">{CATEGORY_LABEL[cat]}</span>
            </span>
            <span className="font-mono text-xs text-[#9aa]">{formatArea(breakdown[cat])}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
