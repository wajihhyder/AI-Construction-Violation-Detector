import { useEffect, useMemo, useState } from 'react'

import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { KARACHI_AREA_LABELS } from '../../constants/karachiAreas'
import type { RoleName } from '../../types/user'

type Props = {
  existingRoles: RoleName[]
  onCreated: () => void
  onCancel: () => void
  submit: (body: {
    username: string
    email: string
    password: string
    role_name: RoleName
    assigned_area?: string | null
  }) => Promise<unknown>
}

export function CreateUser({ existingRoles, onCreated, onCancel, submit }: Props) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [roleName, setRoleName] = useState<RoleName>('AUTHORITY')
  const [assignedArea, setAssignedArea] = useState('')
  const [loading, setLoading] = useState(false)
  const unavailableRoles = useMemo(
    () => new Set<RoleName>(existingRoles.filter((role) => role === 'ADMIN' || role === 'DG')),
    [existingRoles],
  )
  const roleOptions = useMemo(
    () =>
      [
        { value: 'AUTHORITY', label: 'Authority' },
        !unavailableRoles.has('DG') ? { value: 'DG', label: 'Director General (DG)' } : null,
        !unavailableRoles.has('ADMIN') ? { value: 'ADMIN', label: 'Admin' } : null,
      ].filter((option): option is { value: RoleName; label: string } => option !== null),
    [unavailableRoles],
  )

  useEffect(() => {
    if (unavailableRoles.has(roleName)) {
      setRoleName('AUTHORITY')
    }
  }, [roleName, unavailableRoles])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password.length < 8) return
    if (roleName === 'AUTHORITY' && !assignedArea) return
    setLoading(true)
    try {
      await submit({
        username,
        email,
        password,
        role_name: roleName,
        assigned_area: roleName === 'AUTHORITY' ? assignedArea : null,
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
        options={roleOptions}
        value={roleName}
        onChange={(e) => setRoleName(e.target.value as RoleName)}
      />
      {unavailableRoles.size > 0 && (
        <p className="text-xs text-[#666]">
          {[
            unavailableRoles.has('ADMIN') ? 'Admin already exists' : null,
            unavailableRoles.has('DG') ? 'DG already exists' : null,
          ]
            .filter(Boolean)
            .join(' · ')}
        </p>
      )}
      {roleName === 'AUTHORITY' && (
        <Select
          label="Assigned area"
          options={KARACHI_AREA_LABELS.map((label) => ({ value: label, label }))}
          value={assignedArea}
          onChange={(e) => setAssignedArea(e.target.value)}
          required
        />
      )}
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
