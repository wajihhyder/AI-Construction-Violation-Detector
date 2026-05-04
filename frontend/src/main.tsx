import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'

import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: '#111111',
          color: '#fff',
          border: '1px solid #333',
        },
        success: {
          iconTheme: { primary: '#000', secondary: '#fff' },
        },
        error: {
          iconTheme: { primary: '#fff', secondary: '#000' },
        },
      }}
    />
  </StrictMode>,
)
