import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { isAxiosError } from 'axios'

import { submitReport, trackReport } from '../../api/citizen'
import { Navbar } from '../../components/layout/Navbar'
import { TrackComplaintResult } from '../../components/shared/TrackComplaintResult'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import type { CitizenReportPoll } from '../../types/report'
import { DistrictStep } from './DistrictStep'
import { ProcessingStep } from './ProcessingStep'
import { ResultStep } from './ResultStep'
import { UploadStep } from './UploadStep'

type Step = 1 | 2 | 3 | 4

export function CitizenDashboard() {
  const [step, setStep] = useState<Step>(1)
  const [file, setFile] = useState<File | null>(null)
  const [inputType, setInputType] = useState<'street' | 'aerial'>('street')
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null)
  const [reportId, setReportId] = useState<number | null>(null)
  const [trackingId, setTrackingId] = useState<string | null>(null)
  const [resultData, setResultData] = useState<CitizenReportPoll | null>(null)

  const [trackingInput, setTrackingInput] = useState('')
  const [trackLoading, setTrackLoading] = useState(false)
  const [trackRefreshing, setTrackRefreshing] = useState(false)
  const [trackError, setTrackError] = useState<string | null>(null)
  const [trackResult, setTrackResult] = useState<CitizenReportPoll | null>(null)

  async function handleSubmitDistrict(district: string) {
    if (!file) return
    const fd = new FormData()
    fd.append('image', file)
    fd.append('input_type', inputType)
    fd.append('reporter_type', 'Citizen')
    fd.append('district_location', district)
    if (gps != null) {
      fd.append('gps_lat', String(gps.lat))
      fd.append('gps_lng', String(gps.lng))
    }
    const res = await submitReport(fd)
    setReportId(res.report_id)
    setTrackingId(res.tracking_id)
    setStep(3)
  }

  async function handleTrackSubmit(e: React.FormEvent) {
    e.preventDefault()
    const tid = trackingInput.trim().toUpperCase().replace(/\s/g, '')
    if (!tid) return
    setTrackLoading(true)
    setTrackError(null)
    try {
      const data = await trackReport(tid)
      setTrackResult(data)
    } catch (err) {
      setTrackResult(null)
      if (isAxiosError(err) && err.response?.status === 404) {
        setTrackError('No report found. Please check your Tracking ID and try again.')
      } else {
        setTrackError('Something went wrong. Please try again.')
      }
    } finally {
      setTrackLoading(false)
    }
  }

  async function handleTrackRefresh() {
    if (!trackResult?.tracking_id) return
    setTrackRefreshing(true)
    setTrackError(null)
    try {
      const data = await trackReport(trackResult.tracking_id)
      setTrackResult(data)
    } catch {
      setTrackError('Could not refresh. Try again.')
    } finally {
      setTrackRefreshing(false)
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <section className="mb-10 rounded-[var(--radius-lg)] border border-[#333] bg-[#0a0a0a]/80 p-6">
          <h2 className="text-lg font-semibold text-white">Already submitted a report?</h2>
          <form onSubmit={handleTrackSubmit} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="min-w-0 flex-1">
              <Input
                label="Tracking ID"
                placeholder="VS-YYYYMMDD-XXXXX"
                value={trackingInput}
                onChange={(e) => setTrackingInput(e.target.value.toUpperCase().replace(/\s/g, ''))}
                disabled={trackLoading}
                className="font-mono"
              />
            </div>
            <Button type="submit" disabled={trackLoading || !trackingInput.trim()} className="shrink-0">
              {trackLoading ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Tracking…
                </span>
              ) : (
                'Track Complaint'
              )}
            </Button>
          </form>
          <p className="mt-2 text-xs text-[#555]">Enter your Tracking ID to check the status</p>
          {trackError && <p className="mt-3 text-sm text-g-red">{trackError}</p>}
          {trackResult && (
            <div className="mt-6">
              <TrackComplaintResult
                data={trackResult}
                onClose={() => {
                  setTrackResult(null)
                  setTrackError(null)
                  setTrackingInput('')
                }}
                onRefresh={handleTrackRefresh}
                refreshing={trackRefreshing}
              />
            </div>
          )}
        </section>

        <h1 className="mb-2 text-2xl font-semibold">Report a violation</h1>
        <p className="mb-8 text-sm text-[#888]">
          Step {step} of 4 — images are analyzed asynchronously by SBCA workflows.
        </p>

        <Card className="p-6 md:p-8">
          {step === 1 && (
            <UploadStep
              onNext={({ file: f, inputType: it, gps: g }) => {
                setFile(f)
                setInputType(it)
                setGps(g)
                setStep(2)
              }}
            />
          )}
          {step === 2 && file && (
            <DistrictStep gps={gps} onSubmitReport={handleSubmitDistrict} />
          )}
          {step === 3 && reportId !== null && trackingId !== null && (
            <ProcessingStep
              reportId={reportId}
              trackingId={trackingId}
              onDone={(data) => {
                setResultData(data)
                setStep(4)
              }}
            />
          )}
          {step === 4 && resultData && (
            <ResultStep
              data={resultData}
              onReset={() => {
                setStep(1)
                setFile(null)
                setReportId(null)
                setTrackingId(null)
                setResultData(null)
                setGps(null)
              }}
            />
          )}
        </Card>
      </main>
    </div>
  )
}
