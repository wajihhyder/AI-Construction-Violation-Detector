import exifr from 'exifr'

function isValidPair(lat: unknown, lng: unknown): lat is number {
  return typeof lat === 'number' && typeof lng === 'number' && Number.isFinite(lat) && Number.isFinite(lng)
}

/**
 * Read GPS from EXIF / XMP. PNG eXIf and some JPEGs need a large firstChunkSize
 * (metadata can sit far into the file). XMP can carry location when TIFF GPS is absent.
 */
export async function extractGpsFromImageFile(file: File): Promise<{ lat: number; lng: number } | null> {
  const maxBytes = Math.min(file.size, 12 * 1024 * 1024)
  const common = {
    gps: true,
    xmp: true,
    tiff: true,
    mergeOutput: true,
    reviveValues: true,
    firstChunkSize: maxBytes,
  } as const

  const tryParse = async (input: File | ArrayBuffer) => {
    const parsed = await exifr.parse(input, { ...common, firstChunkSize: maxBytes })
    if (parsed && isValidPair(parsed.latitude, parsed.longitude)) {
      return { lat: parsed.latitude, lng: parsed.longitude }
    }
    return null
  }

  try {
    const a = await tryParse(file)
    if (a) return a

    const g = await exifr.gps(file)
    if (g && isValidPair(g.latitude, g.longitude)) {
      return { lat: g.latitude, lng: g.longitude }
    }

    // Last resort: parse the full buffer so late eXIf / APP1 segments are included
    const buf = await file.arrayBuffer()
    if (buf.byteLength > 0) {
      const b = await exifr.parse(buf, { ...common, firstChunkSize: buf.byteLength })
      if (b && isValidPair(b.latitude, b.longitude)) {
        return { lat: b.latitude, lng: b.longitude }
      }
      const g2 = await exifr.gps(buf)
      if (g2 && isValidPair(g2.latitude, g2.longitude)) {
        return { lat: g2.latitude, lng: g2.longitude }
      }
    }
  } catch {
    /* drop to null */
  }
  return null
}
