import { useEffect, useState } from 'react'

import type { AdminUser } from '../../api/admin'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'

type Props = {
  user: AdminUser
  onSaved: () => void
  onCancel: () => void
  submit: (
    id: number,
    body: Partial<{ username: string; email: string; password: string; role: boolean }>,
  ) => Promise<unknown>
}

export function EditUser({ user, onSaved, onCancel, submit }: Props) {
  const [username, setUsername] = useState(user.username)
  const [email, setEmail] = useState(user.email)
  const [password, setPassword] = useState('')
  const [role, setRole] = useState(user.role ? 'admin' : 'authority')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setUsername(user.username)
    setEmail(user.email)
    setRole(user.role ? 'admin' : 'authority')
    setPassword('')
  }, [user])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const body: Partial<{ username: string; email: string; password: string; role: boolean }> = {
        username,
        email,
        role: role === 'admin',
      }
      if (password.length >= 8) body.password = password
      await submit(user.id, body)
      onSaved()
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
      <Input
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <Input
        label="New password (optional)"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Leave blank to keep current"
      />
      <Select
        label="Role"
        options={[
          { value: 'authority', label: 'Authority' },
          { value: 'admin', label: 'Admin' },
        ]}
        value={role}
        onChange={(e) => setRole(e.target.value)}
      />
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          Save
        </Button>
      </div>
    </form>
  )
}
