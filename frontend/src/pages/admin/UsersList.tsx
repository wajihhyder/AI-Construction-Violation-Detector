import { format } from 'date-fns'
import { Pencil, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

import {
  createUser,
  deleteUser,
  fetchUsers,
  updateUser,
  type AdminUser,
} from '../../api/admin'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { CreateUser } from './CreateUser'
import { EditUser } from './EditUser'

export function UsersList() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    try {
      const list = await fetchUsers()
      setUsers(list)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id: number) {
    try {
      await deleteUser(id)
      toast.success('User deleted')
      setDeleteId(null)
      load()
    } catch {
      /* interceptor */
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Users</h1>
          <p className="text-sm text-[#888]">Authority and admin accounts</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>Add New User</Button>
      </div>

      <div className="mt-8 overflow-x-auto rounded-[var(--radius-lg)] border border-[#333]">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-[#222] bg-[#0a0a0a] text-xs uppercase text-[#555]">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Last login</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[#555]">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-[#555]">
                  No users found.
                </td>
              </tr>
            )}
            {!loading &&
              users.map((u) => (
                <tr key={u.id} className="border-b border-[#222] hover:bg-[#0a0a0a]/80">
                  <td className="px-4 py-3 font-mono">{u.id}</td>
                  <td className="px-4 py-3">{u.username}</td>
                  <td className="px-4 py-3 text-[#888]">{u.email}</td>
                  <td className="px-4 py-3">
                    {u.role ? (
                      <span className="rounded-full border border-white/35 bg-white/10 px-2 py-0.5 text-xs text-white">
                        Admin
                      </span>
                    ) : (
                      <span className="rounded-full border border-[#333] px-2 py-0.5 text-xs text-[#888]">
                        Authority
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[#888]">
                    {u.last_login ? format(new Date(u.last_login), 'PPp') : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      className="mr-2 inline-flex text-[#888] hover:text-white"
                      aria-label="Edit"
                      onClick={() => setEditUser(u)}
                    >
                      <Pencil size={18} />
                    </button>
                    <button
                      type="button"
                      className="inline-flex text-[#888] hover:text-white"
                      aria-label="Delete"
                      onClick={() => setDeleteId(u.id)}
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create user">
        <CreateUser
          onCancel={() => setCreateOpen(false)}
          onCreated={() => {
            setCreateOpen(false)
            toast.success('User created')
            load()
          }}
          submit={createUser}
        />
      </Modal>

      <Modal
        open={!!editUser}
        onClose={() => setEditUser(null)}
        title="Edit user"
      >
        {editUser && (
          <EditUser
            user={editUser}
            onCancel={() => setEditUser(null)}
            onSaved={() => {
              setEditUser(null)
              toast.success('User updated')
              load()
            }}
            submit={updateUser}
          />
        )}
      </Modal>

      <Modal open={deleteId !== null} onClose={() => setDeleteId(null)} title="Confirm delete">
        <p className="text-sm text-[#888]">This cannot be undone.</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDeleteId(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={() => deleteId && handleDelete(deleteId)}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  )
}
