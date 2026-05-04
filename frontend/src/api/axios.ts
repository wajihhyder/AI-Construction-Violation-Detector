import axios from 'axios'
import toast from 'react-hot-toast'

import { API_BASE_URL } from '../config'
import { useAuthStore } from '../store/authStore'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  // Avoid sending JSON Content-Type on GET/HEAD (no body); some stacks mishandle it for HTML endpoints.
  const method = (config.method ?? 'get').toLowerCase()
  if (method === 'get' || method === 'head') {
    delete config.headers['Content-Type']
  }
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Collapses duplicate rapid toasts (e.g. two failing actions in a row). */
function toastApi(text: string) {
  toast.error(text, { id: 'construction-violation-api-error' })
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = String(err.config?.url ?? '')
    const isLogin = url.includes('/api/auth/login')
    const status = err.response?.status
    const data = err.response?.data
    let message = 'Something went wrong. Please try again.'
    if (data?.detail) {
      if (typeof data.detail === 'string') message = data.detail
      else if (typeof data.detail?.detail === 'string') message = data.detail.detail
    }
    if (status === 401 && !isLogin) {
      useAuthStore.getState().logout()
      toast.error('Session expired')
      window.location.href = '/login'
    } else if (status === 413) {
      toast.error('Image too large (max 10MB)')
    } else if (!status) {
      toastApi(
        'Cannot reach the API. Start FastAPI on port 8000 (`cd backend` → `uvicorn main:app --reload --port 8000`) while using `npm run dev` / `npm run preview`.',
      )
    } else if (status === 502 || status === 503 || status === 504) {
      toastApi(
        'Bad gateway — the dev server could not reach the API on port 8000. Start the backend, then retry.',
      )
    } else if (status >= 500) {
      toastApi('Something went wrong. Please try again.')
    } else if (status !== 401 && !(isLogin && status === 401)) {
      const skip404Track =
        status === 404 && typeof url === 'string' && url.includes('/api/citizen/track/')
      if (!skip404Track) toastApi(message)
    }
    return Promise.reject(err)
  },
)
