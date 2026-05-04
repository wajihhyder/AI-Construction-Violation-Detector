import { ImageIcon } from 'lucide-react'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

import { Button } from '../ui/Button'
import { extractGpsFromImageFile } from '../../utils/extractGps'

type Props = {
  onFile: (file: File, previewUrl: string, gps: { lat: number; lng: number } | null) => void
  maxMb?: number
}

export function ImageDropzone({ onFile, maxMb = 10 }: Props) {
  const [preview, setPreview] = useState<string | null>(null)
  const [warnNoGps, setWarnNoGps] = useState(false)

  const onDrop = useCallback(
    async (accepted: File[]) => {
      const file = accepted[0]
      if (!file) return
      if (file.size > maxMb * 1024 * 1024) return

      let gps: { lat: number; lng: number } | null = null
      try {
        gps = await extractGpsFromImageFile(file)
        if (gps) {
          setWarnNoGps(false)
        } else {
          setWarnNoGps(true)
        }
      } catch {
        setWarnNoGps(true)
      }

      const url = URL.createObjectURL(file)
      setPreview(url)
      onFile(file, url, gps)
    },
    [maxMb, onFile],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'] },
    maxFiles: 1,
    maxSize: maxMb * 1024 * 1024,
  })

  return (
    <div>
      {warnNoGps && (
        <div className="mb-3 rounded-[var(--radius-md)] border border-white/35 bg-white/10 px-3 py-2 text-sm text-[#ddd]">
          No GPS found — you&apos;ll select district manually
        </div>
      )}
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-[var(--radius-lg)] border-2 border-dashed border-[#333] bg-[#0a0a0a] p-8 transition-colors hover:border-white/50 ${
          isDragActive ? 'border-white' : ''
        }`}
      >
        <input {...getInputProps()} />
        <ImageIcon className="mb-2 text-white" size={36} />
        <p className="text-center text-sm text-[#888]">
          Drag & drop an image, or{' '}
          <span className="text-white underline">browse</span> (JPG/PNG, max {maxMb}MB)
        </p>
      </div>
      {preview && (
        <div className="mt-4">
          <img src={preview} alt="Preview" className="max-h-64 rounded-[var(--radius-md)] border border-[#333]" />
          <Button
            variant="secondary"
            className="mt-2 !text-xs"
            onClick={(e) => {
              e.stopPropagation()
              setPreview(null)
              setWarnNoGps(false)
            }}
          >
            Clear
          </Button>
        </div>
      )}
    </div>
  )
}
