import { useState } from 'react'

import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'

type Props = {
  onCreated: () => void
  onCancel: () => void
  submit: (body: {
    username: string
    email: string
    password: string
    role: boolean
  }) => Promise<unknown>
}

export function CreateUser({ onCreated, onCancel, submit }: Props) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('authority')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password.length < 8) return
    setLoading(true)
    try {
      await submit({
        username,
        email,
        password,
        role: role === 'admin',
      })
      onCreated()
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
        label="Password (min 8)"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
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
          Create
        </Button>
      </div>
    </form>
  )
}
