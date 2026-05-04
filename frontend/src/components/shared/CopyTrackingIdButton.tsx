import { useState } from 'react'

import { Button } from '../ui/Button'

type Props = { trackingId: string; className?: string }

export function CopyTrackingIdButton({ trackingId, className }: Props) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(trackingId)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <Button type="button" variant="secondary" className={className} onClick={() => void copy()}>
      {copied ? '✓ Copied!' : 'Copy ID'}
    </Button>
  )
}
