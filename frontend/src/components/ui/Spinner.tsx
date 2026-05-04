import clsx from 'clsx'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        'h-8 w-8 animate-spin rounded-full border-2 border-[#333] border-t-white',
        className,
      )}
      aria-hidden
    />
  )
}
