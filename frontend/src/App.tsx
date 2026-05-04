import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AdminLayout } from './pages/admin/AdminLayout'
import { UsersList } from './pages/admin/UsersList'
import { AuthorityLayout } from './pages/authority/AuthorityLayout'
import { MapDashboard } from './pages/authority/MapDashboard'
import { ReportDetail } from './pages/authority/ReportDetail'
import { ReportsList } from './pages/authority/ReportsList'
import { CitizenDashboard } from './pages/citizen/CitizenDashboard'
import { Landing } from './pages/Landing'
import { Login } from './pages/Login'
import { TrackReport } from './pages/TrackReport'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/citizen" element={<CitizenDashboard />} />
        <Route path="/track" element={<TrackReport />} />
        <Route path="/track/:trackingId" element={<TrackReport />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/authority" element={<AuthorityLayout />}>
            <Route index element={<Navigate to="reports" replace />} />
            <Route path="reports" element={<ReportsList />} />
            <Route path="reports/:reportId" element={<ReportDetail />} />
            <Route path="map" element={<MapDashboard />} />
          </Route>
        </Route>

        <Route element={<ProtectedRoute adminOnly />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="users" replace />} />
            <Route path="users" element={<UsersList />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
