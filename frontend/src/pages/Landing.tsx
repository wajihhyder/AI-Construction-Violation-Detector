import { Camera, Cpu, FileImage } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Navbar } from '../components/layout/Navbar'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { APP_DISPLAY_NAME } from '../constants/branding'

export function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-16 pt-12">
        <section className="relative overflow-hidden rounded-[var(--radius-xl)] border border-[#222] bg-[#0a0a0a]/80 px-8 py-16 text-center shadow-[0_0_0_1px_#222]">
          <div
            className="pointer-events-none absolute inset-0 opacity-30"
            style={{
              backgroundImage: 'radial-gradient(#333 1px, transparent 1px)',
              backgroundSize: '24px 24px',
            }}
          />
          <h1 className="relative text-2xl font-semibold tracking-tight sm:text-3xl md:text-4xl lg:text-5xl">
            {APP_DISPLAY_NAME}
          </h1>
          <p className="relative mx-auto mt-4 max-w-2xl text-lg text-[#888]">
            AI-Powered Construction Violation Detection for Karachi
          </p>
          <div className="relative mt-10 flex flex-wrap justify-center gap-4">
            <Link to="/citizen">
              <Button className="px-8 py-3 text-base">Report a Violation</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" className="border border-[#333] px-8 py-3 text-base">
                Authority Login
              </Button>
            </Link>
          </div>
        </section>

        <section className="mt-14 grid gap-6 md:grid-cols-3">
          {[
            {
              icon: FileImage,
              title: 'Upload Image',
              desc: 'Submit street-view or aerial imagery with optional GPS metadata.',
            },
            {
              icon: Cpu,
              title: 'AI Detection',
              desc: 'Automated screening flags potential violations for SBCA review.',
            },
            {
              icon: Camera,
              title: 'Instant Report',
              desc: 'Receive structured results with district context and evidence.',
            },
          ].map((f) => (
            <Card key={f.title} hover className="p-6">
              <f.icon className="mb-3 text-white" size={28} />
              <h3 className="text-lg font-medium">{f.title}</h3>
              <p className="mt-2 text-sm text-[#888]">{f.desc}</p>
            </Card>
          ))}
        </section>

        <footer className="mt-16 border-t border-[#222] pt-8 text-center text-xs text-[#555]">
          {APP_DISPLAY_NAME} — Sindh Building Control Authority citizen reporting prototype · Karachi,
          Pakistan
        </footer>
      </main>
    </div>
  )
}
