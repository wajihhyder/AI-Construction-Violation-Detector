import { Outlet } from 'react-router-dom'

import { Sidebar } from '../../components/layout/Sidebar'

export function AdminLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar variant="admin" />
      <div className="flex-1 overflow-auto bg-black">
        <Outlet />
      </div>
    </div>
  )
}
