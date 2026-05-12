import { Navigate, Outlet } from 'react-router-dom'

import { useAuthStore } from '../../store/authStore'

type Props = { adminOnly?: boolean }

export function ProtectedRoute({ adminOnly }: Props) {
  const { token, user } = useAuthStore()
  if (!token || !user) {
    return <Navigate to="/login" replace />
  }
  const isAdmin = user.roleName ? user.roleName === 'ADMIN' : user.role
  if (adminOnly && !isAdmin) {
    return <Navigate to="/authority/reports" replace />
  }
  return <Outlet />
}
