import clsx from 'clsx'
import type { ButtonHTMLAttributes } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'warning'
}

export function Button({ variant = 'primary', className, children, type = 'button', ...rest }: Props) {
  return (
    <button
      type={type}
      className={clsx(
        'rounded-[var(--radius-md)] px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out disabled:opacity-50',
        variant === 'primary' &&
          'bg-white text-black hover:bg-[#e0e0e0] shadow-[0_0_0_1px_#222]',
        variant === 'secondary' &&
          'border border-[#333] bg-transparent text-white hover:bg-[#1a1a1a]',
        variant === 'danger' &&
          'border border-[#666] bg-[#2a2a2a] text-white hover:bg-[#3a3a3a]',
        variant === 'warning' &&
          'border border-[#888] bg-[#444] text-white hover:bg-[#555]',
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  )
}
