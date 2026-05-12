import clsx from 'clsx'

const MAP: Record<string, string> = {
  Extra_Floor: 'border border-white/25 bg-white/10 text-white',
  Setback_Breach: 'border border-[#888]/40 bg-[#888]/15 text-[#ddd]',
  Encroachment: 'border border-[#666]/50 bg-[#666]/20 text-[#eee]',
  Manual_Review: 'border border-[#777]/50 bg-[#777]/15 text-[#ddd]',
}

export function ViolationBadge({ type }: { type: string | null }) {
  if (!type) return <span className="text-xs text-[#555]">—</span>
  return (
    <span
      className={clsx(
        'rounded-full px-2 py-0.5 text-xs font-medium',
        MAP[type] ?? 'bg-[#333] text-[#aaa]',
      )}
    >
      {type.replace('_', ' ')}
    </span>
  )
}
