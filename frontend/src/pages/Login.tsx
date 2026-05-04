import { Building2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { login as loginApi } from '../api/auth'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { APP_DISPLAY_NAME } from '../constants/branding'
import { useAuthStore } from '../store/authStore'

export function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await loginApi({ username, password })
      setAuth({
        token: data.access_token,
        userId: data.user_id,
        username: data.username,
        role: data.role,
      })
      if (data.role) {
        navigate('/admin/users', { replace: true })
      } else {
        navigate('/authority/reports', { replace: true })
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: unknown } } }
      const d = ax.response?.data?.detail
      const msg =
        typeof d === 'string'
          ? d
          : typeof d === 'object' && d && 'detail' in d
            ? String((d as { detail: string }).detail)
            : 'Invalid credentials'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 flex flex-col items-center gap-2">
          <Building2 className="text-white" size={40} />
          <h1 className="text-center text-lg font-semibold leading-snug sm:text-xl">{APP_DISPLAY_NAME}</h1>
          <p className="text-sm text-[#888]">Authority &amp; admin sign in</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <Input
            label="Password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && (
            <p className="text-sm text-[#ccc]" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>
        <p className="mt-6 text-center text-xs text-[#555]">
          No public registration —{' '}
          <Link className="text-white hover:underline" to="/">
            Back home
          </Link>
        </p>
      </Card>
    </div>
  )
}
