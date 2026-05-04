import clsx from 'clsx'
import type { HTMLAttributes } from 'react'

type Props = HTMLAttributes<HTMLDivElement> & {
  children: React.ReactNode
  hover?: boolean
}

export function Card({ children, className, hover, ...rest }: Props) {
  return (
    <div
      {...rest}
      className={clsx(
        'rounded-[var(--radius-lg)] border border-[#333] bg-[#111] shadow-[0_0_0_1px_#222]',
        hover && 'transition-transform duration-200 hover:-translate-y-0.5',
        className,
      )}
    >
      {children}
    </div>
  )
}
