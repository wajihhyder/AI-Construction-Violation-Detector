import { api } from './axios'

export type LoginBody = { username: string; password: string }

export type LoginRes = {
  access_token: string
  token_type: string
  role: boolean
  username: string
  user_id: number
}

export async function login(body: LoginBody) {
  const { data } = await api.post<LoginRes>('/api/auth/login', body)
  return data
}

export async function fetchMe() {
  const { data } = await api.get<{ id: number; username: string; email: string; role: boolean }>(
    '/api/auth/me',
  )
  return data
}
