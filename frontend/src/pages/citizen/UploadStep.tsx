import { useState } from 'react'

import { ImageDropzone } from '../../components/shared/ImageDropzone'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'

type InputKind = 'street' | 'aerial'

type Props = {
  onNext: (payload: {
    file: File
    inputType: InputKind
    gps: { lat: number; lng: number } | null
  }) => void
}

export function UploadStep({ onNext }: Props) {
  const [inputType, setInputType] = useState<InputKind>('street')
  const [file, setFile] = useState<File | null>(null)
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card
          hover
          className={`cursor-pointer p-6 transition-all ${inputType === 'street' ? 'ring-2 ring-white' : ''}`}
          onClick={() => setInputType('street')}
        >
          <h3 className="text-lg font-medium">Street View</h3>
          <p className="mt-2 text-sm text-[#888]">
            Ground-level photo of the building facade — best for floor-count screening.
          </p>
        </Card>
        <Card
          hover
          className={`cursor-pointer p-6 transition-all ${inputType === 'aerial' ? 'ring-2 ring-white' : ''}`}
          onClick={() => setInputType('aerial')}
        >
          <h3 className="text-lg font-medium">Aerial / Satellite</h3>
          <p className="mt-2 text-sm text-[#888]">
            Top-down imagery — setback and boundary compliance cues.
          </p>
        </Card>
      </div>

      <ImageDropzone
        onFile={(f, _url, g) => {
          setFile(f)
          setGps(g)
        }}
      />

      <div className="flex justify-end">
        <Button
          disabled={!file}
          onClick={() => {
            if (file) onNext({ file, inputType, gps })
          }}
        >
          Continue
        </Button>
      </div>
    </div>
  )
}
