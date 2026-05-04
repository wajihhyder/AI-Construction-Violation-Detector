import { Building2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '../ui/Button'
import { APP_DISPLAY_NAME } from '../../constants/branding'
import { useAuthStore } from '../../store/authStore'

export function Navbar() {
  const { user, logout } = useAuthStore()

  return (
    <header className="border-b border-[#222] bg-black/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex max-w-[min(100vw-10rem,28rem)] items-center gap-2 font-semibold tracking-tight">
          <Building2 className="shrink-0 text-white" />
          <span className="text-left text-sm leading-snug sm:text-base">{APP_DISPLAY_NAME}</span>
        </Link>
        <nav className="flex items-center gap-3">
          <Link
            to="/citizen"
            className="text-sm text-[#888] transition-colors hover:text-white"
          >
            Report
          </Link>
          {!user && (
            <Link to="/login">
              <Button variant="secondary" className="!py-1.5 !text-xs">
                Authority Login
              </Button>
            </Link>
          )}
          {user && !user.role && (
            <Link to="/authority/reports" className="text-sm text-[#888] hover:text-white">
              Dashboard
            </Link>
          )}
          {user && user.role && (
            <>
              <Link to="/authority/reports" className="text-sm text-[#888] hover:text-white">
                Authority
              </Link>
              <Link to="/admin/users" className="text-sm text-[#888] hover:text-white">
                Admin
              </Link>
            </>
          )}
          {user && (
            <Button
              variant="secondary"
              className="!py-1.5 !text-xs"
              onClick={() => {
                logout()
                window.location.href = '/'
              }}
            >
              Logout
            </Button>
          )}
        </nav>
      </div>
    </header>
  )
}
