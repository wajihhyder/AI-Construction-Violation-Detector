import clsx from 'clsx'

const STATUS_MAP: Record<string, string> = {
  New: 'bg-white/15 text-white border-white/35',
  Processing: 'bg-[#888]/25 text-[#ccc] border-[#888]/45',
  Under_Review: 'bg-[#666]/30 text-[#ddd] border-[#888]/50',
  Verified: 'bg-white/10 text-white border-white/30',
  Invalid: 'bg-black/40 text-[#aaa] border-[#555]',
}

type Props = { children: React.ReactNode; status?: string; className?: string }

export function Badge({ children, status, className }: Props) {
  const key = status ?? String(children)
  const styles = STATUS_MAP[key] ?? 'bg-[#333]/40 text-[#ccc] border-[#444]'
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        styles,
        className,
      )}
    >
      {children}
    </span>
  )
}
