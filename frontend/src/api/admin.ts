import { api } from './axios'

export type AdminUser = {
  id: number
  username: string
  email: string
  role: boolean
  last_login: string | null
}

export async function fetchUsers() {
  const { data } = await api.get<AdminUser[]>('/api/admin/users')
  return data
}

export async function createUser(body: {
  username: string
  email: string
  password: string
  role: boolean
}) {
  const { data } = await api.post<AdminUser>('/api/admin/users', body)
  return data
}

export async function updateUser(
  id: number,
  body: Partial<{ username: string; email: string; password: string; role: boolean }>,
) {
  const { data } = await api.put<AdminUser>(`/api/admin/users/${id}`, body)
  return data
}

export async function deleteUser(id: number) {
  await api.delete(`/api/admin/users/${id}`)
}
