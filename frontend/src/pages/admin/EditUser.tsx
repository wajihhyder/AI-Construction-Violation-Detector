import { useEffect, useState } from 'react'

import type { AdminUser } from '../../api/admin'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { KARACHI_AREA_LABELS } from '../../constants/karachiAreas'
import type { RoleName } from '../../types/user'

type Props = {
  user: AdminUser
  onSaved: () => void
  onCancel: () => void
  submit: (
    id: number,
    body: Partial<{
      username: string
      email: string
      password: string
      role_name: RoleName
      assigned_area: string | null
    }>,
  ) => Promise<unknown>
}

export function EditUser({ user, onSaved, onCancel, submit }: Props) {
  const [username, setUsername] = useState(user.username)
  const [email, setEmail] = useState(user.email)
  const [password, setPassword] = useState('')
  const [assignedArea, setAssignedArea] = useState(user.assigned_area ?? '')
  const [loading, setLoading] = useState(false)
  const hasMissingLegacyArea = user.role_name === 'AUTHORITY' && !user.assigned_area

  useEffect(() => {
    setUsername(user.username)
    setEmail(user.email)
    setAssignedArea(user.assigned_area ?? '')
    setPassword('')
  }, [user])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const body: Partial<{
        username: string
        email: string
        password: string
        role_name: RoleName
        assigned_area: string | null
      }> = {
        username,
        email,
      }
      if (password.length >= 8) body.password = password
      if (user.role_name === 'AUTHORITY') {
        const normalizedAssignedArea = assignedArea.trim()
        if (normalizedAssignedArea || user.assigned_area) {
          body.assigned_area = normalizedAssignedArea || null
        }
      }
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
      <Input
        label="Role"
        value={user.role_name === 'ADMIN' ? 'Admin' : user.role_name === 'DG' ? 'Director General (DG)' : 'Authority'}
        readOnly
      />
      {user.role_name === 'AUTHORITY' && (
        <>
          <Select
            label="Assigned area"
            options={[
              ...(hasMissingLegacyArea ? [{ value: '', label: 'Leave unassigned for now' }] : []),
              ...KARACHI_AREA_LABELS.map((label) => ({ value: label, label })),
            ]}
            value={assignedArea}
            onChange={(e) => setAssignedArea(e.target.value)}
            required={!hasMissingLegacyArea}
          />
          {hasMissingLegacyArea && (
            <p className="text-xs text-[#666]">
              This legacy authority user has no assigned area yet. You can save other changes now, or assign a town
              to enable scoped access.
            </p>
          )}
        </>
      )}
      {(user.role_name === 'ADMIN' || user.role_name === 'DG') && (
        <p className="text-xs text-[#666]">Protected roles cannot be reassigned or deleted.</p>
      )}
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
