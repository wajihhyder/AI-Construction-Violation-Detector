export type RoleName = 'ADMIN' | 'AUTHORITY' | 'DG'

export type AuthUser = {
  userId: number
  username: string
  role: boolean
  roleName: RoleName
  assignedArea: string | null
  token: string
}
