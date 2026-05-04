import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { AuthUser } from '../types/user'

type AuthState = {
  user: Omit<AuthUser, 'token'> | null
  token: string | null
  setAuth: (user: AuthUser) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (u) =>
        set({
          token: u.token,
          user: { userId: u.userId, username: u.username, role: u.role },
        }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'acvd-auth' },
  ),
)
