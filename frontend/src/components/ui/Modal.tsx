import { X } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
}

export function Modal({ open, onClose, title, children }: Props) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-[var(--radius-xl)] border border-[#333] bg-[#111] p-6 shadow-xl"
        role="dialog"
        aria-modal
      >
        <button
          type="button"
          className="absolute right-4 top-4 text-[#888] hover:text-white"
          onClick={onClose}
          aria-label="Close"
        >
          <X size={20} />
        </button>
        {title && <h2 className="mb-4 text-lg font-semibold">{title}</h2>}
        {children}
      </div>
    </div>
  )
}
