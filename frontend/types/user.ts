export type Role = {
  id: string
  name: string
}

export type User = {
  id: string
  username: string
  name: string
  role: Role
}

export type UserSession = {
  user?: User
}
