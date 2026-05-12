import { BarChart3, LogOut, Map, User } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { APP_DISPLAY_NAME } from '../../constants/branding'
import { useAuthStore } from '../../store/authStore'

const linkCls = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-[var(--radius-md)] px-3 py-2 text-sm transition-colors ${
    isActive ? 'bg-[#1a1a1a] text-white' : 'text-[#888] hover:bg-[#111] hover:text-white'
  }`

export function Sidebar({ variant }: { variant: 'authority' | 'admin' }) {
  const { user, logout } = useAuthStore()
  const roleLabel =
    user?.roleName === 'ADMIN'
      ? 'Admin'
      : user?.roleName === 'DG'
        ? 'Director General'
        : user?.role
          ? 'Admin'
          : 'Authority'

  return (
    <aside className="flex h-full w-56 flex-col border-r border-[#222] bg-[#0a0a0a] p-4">
      <div className="mb-6 text-xs font-semibold leading-snug text-[#ccc]">{APP_DISPLAY_NAME}</div>
      {variant === 'authority' && (
        <nav className="flex flex-1 flex-col gap-1">
          <NavLink to="/authority/reports" className={linkCls}>
            <BarChart3 size={18} /> Dashboard
          </NavLink>
          <NavLink to="/authority/map" className={linkCls}>
            <Map size={18} /> Map View
          </NavLink>
        </nav>
      )}
      {variant === 'admin' && (
        <nav className="flex flex-1 flex-col gap-1">
          <NavLink to="/admin/users" className={linkCls}>
            <User size={18} /> Manage Users
          </NavLink>
        </nav>
      )}
      <div className="mt-auto border-t border-[#222] pt-4 text-xs text-[#555]">
        <div className="mb-2 flex items-center gap-2 text-[#888]">
          <User size={14} />
          <span className="truncate">{user?.username}</span>
        </div>
        <div className="mb-1 truncate text-[#666]">{roleLabel}</div>
        {user?.assignedArea && variant === 'authority' && (
          <div className="mb-3 truncate text-[#666]">{user.assignedArea}</div>
        )}
        <button
          type="button"
          className="flex items-center gap-2 text-sm text-[#888] hover:text-white"
          onClick={() => {
            logout()
            window.location.href = '/login'
          }}
        >
          <LogOut size={16} /> Logout
        </button>
      </div>
    </aside>
  )
}
