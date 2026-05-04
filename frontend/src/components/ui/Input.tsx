import clsx from 'clsx'
import type { InputHTMLAttributes } from 'react'

type Props = InputHTMLAttributes<HTMLInputElement> & { label?: string }

export function Input({ label, className, id, ...rest }: Props) {
  const cid = id ?? rest.name
  return (
    <label className="block w-full">
      {label && (
        <span className="mb-1 block text-sm text-[#888]">{label}</span>
      )}
      <input
        id={cid}
        className={clsx(
          'mt-1 w-full rounded-[var(--radius-md)] border border-[#333] bg-[#0a0a0a] px-3 py-2 text-sm text-white placeholder:text-[#555] focus:border-white focus:outline-none focus:ring-1 focus:ring-white',
          className,
        )}
        {...rest}
      />
    </label>
  )
}
