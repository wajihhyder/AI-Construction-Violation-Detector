/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** FastAPI origin (no trailing slash), e.g. http://localhost:8000 */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
