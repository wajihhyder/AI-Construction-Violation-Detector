import clsx from 'clsx'
import type { SelectHTMLAttributes } from 'react'

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string
  options: { value: string; label: string }[]
}

export function Select({ label, options, className, id, ...rest }: Props) {
  const cid = id ?? rest.name
  return (
    <label className="block w-full">
      {label && (
        <span className="mb-1 block text-sm text-[#888]">{label}</span>
      )}
      <select
        id={cid}
        className={clsx(
          'mt-1 w-full rounded-[var(--radius-md)] border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-white focus:border-white focus:outline-none focus:ring-1 focus:ring-white',
          className,
        )}
        {...rest}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
}
