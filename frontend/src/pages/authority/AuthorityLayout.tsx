import { Outlet } from 'react-router-dom'

import { Sidebar } from '../../components/layout/Sidebar'

export function AuthorityLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar variant="authority" />
      <div className="flex-1 overflow-auto bg-black">
        <Outlet />
      </div>
    </div>
  )
}
