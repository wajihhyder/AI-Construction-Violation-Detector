import clsx from 'clsx'

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        'animate-shimmer rounded-md bg-[length:200%_100%] bg-gradient-to-r from-[#1a1a1a] via-[#222] to-[#1a1a1a]',
        className,
      )}
    />
  )
}
