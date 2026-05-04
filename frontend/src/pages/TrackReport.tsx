import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { useNavigate, useParams } from 'react-router-dom'

import { trackReport } from '../api/citizen'
import { Navbar } from '../components/layout/Navbar'
import { TrackComplaintResult } from '../components/shared/TrackComplaintResult'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import type { CitizenReportPoll } from '../types/report'

export function TrackReport() {
  const { trackingId: routeTrackingId } = useParams<{ trackingId: string }>()
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CitizenReportPoll | null>(null)

  useEffect(() => {
    if (!routeTrackingId) return
    const decoded = decodeURIComponent(routeTrackingId)
    setInput(decoded.toUpperCase().replace(/\s/g, ''))
    let cancelled = false
    setLoading(true)
    setError(null)
    setResult(null)
    ;(async () => {
      try {
        const data = await trackReport(decoded)
        if (!cancelled) setResult(data)
      } catch (e) {
        if (!cancelled) {
          setResult(null)
          if (isAxiosError(e) && e.response?.status === 404) {
            setError('No report found. Please check your Tracking ID and try again.')
          } else {
            setError('Something went wrong. Please try again.')
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [routeTrackingId])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const tid = input.trim().toUpperCase().replace(/\s/g, '')
    if (!tid) return
    navigate(`/track/${encodeURIComponent(tid)}`, { replace: true })
  }

  async function handleRefresh() {
    if (!result?.tracking_id) return
    setRefreshing(true)
    setError(null)
    try {
      const data = await trackReport(result.tracking_id)
      setResult(data)
    } catch {
      setError('Could not refresh. Try again.')
    } finally {
      setRefreshing(false)
    }
  }

  function trackAnother() {
    setInput('')
    setResult(null)
    setError(null)
    navigate('/track', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 py-10">
        <h1 className="text-2xl font-semibold">Track a complaint</h1>
        <p className="mt-1 text-sm text-[#888]">Enter the Tracking ID from your submission confirmation.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <Input
            label="Tracking ID"
            placeholder="VS-YYYYMMDD-XXXXX"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase().replace(/\s/g, ''))}
            className="font-mono"
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Tracking…
              </span>
            ) : (
              'Track Complaint'
            )}
          </Button>
        </form>

        {error && <p className="mt-4 text-sm text-g-red">{error}</p>}

        {result && (
          <div className="mt-8 space-y-4">
            <TrackComplaintResult
              data={result}
              onClose={trackAnother}
              onRefresh={handleRefresh}
              refreshing={refreshing}
            />
            <div className="flex justify-center">
              <Button type="button" variant="secondary" onClick={trackAnother}>
                Track Another Report
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
