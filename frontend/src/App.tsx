import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { Spinner } from './components/ui/Spinner'

const AdminLayout = lazy(() => import('./pages/admin/AdminLayout').then((m) => ({ default: m.AdminLayout })))
const UsersList = lazy(() => import('./pages/admin/UsersList').then((m) => ({ default: m.UsersList })))
const AuthorityLayout = lazy(() =>
  import('./pages/authority/AuthorityLayout').then((m) => ({ default: m.AuthorityLayout })),
)
const MapDashboard = lazy(() =>
  import('./pages/authority/MapDashboard').then((m) => ({ default: m.MapDashboard })),
)
const ReportDetail = lazy(() =>
  import('./pages/authority/ReportDetail').then((m) => ({ default: m.ReportDetail })),
)
const ReportsList = lazy(() =>
  import('./pages/authority/ReportsList').then((m) => ({ default: m.ReportsList })),
)
const CitizenDashboard = lazy(() =>
  import('./pages/citizen/CitizenDashboard').then((m) => ({ default: m.CitizenDashboard })),
)
const Landing = lazy(() => import('./pages/Landing').then((m) => ({ default: m.Landing })))
const Login = lazy(() => import('./pages/Login').then((m) => ({ default: m.Login })))
const TrackReport = lazy(() => import('./pages/TrackReport').then((m) => ({ default: m.TrackReport })))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center bg-black">
            <Spinner />
          </div>
        }
      >
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
      </Suspense>
    </BrowserRouter>
  )
}
