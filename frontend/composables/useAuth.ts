import type { User, UserSession } from '~/types/user'

export const useAuth = () => {
  const token = useCookie('access_token')

  const userState = useState<UserSession>('auth_user', () => ({}))

  const isAuthenticated = computed(
    () => !!(userState.value && userState.value.user)
  )

  const loadUser = async () => {
    if (token.value) {
      try {
        const fetchedUser = await useRequestFetch()<User | { message: string }>(
          '/api/auth/me',
          {
            headers: { Authorization: `Bearer ${token.value}` },
          }
        )
        if (fetchedUser) {
          userState.value = { user: fetchedUser as User }
        }
      } catch (err: any) {
        logout()
      }
    }
  }

  const logout = async () => {
    userState.value = {}
    token.value = null
    await navigateTo('/login')
  }

  const login = async (username: string, password: string) => {
    const data = await useRequestFetch()<{ access_token?: string }>(
      '/api/auth/login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }).toString(),
      }
    )

    if (data.access_token) {
      token.value = data.access_token
      await loadUser()
      return true
    }

    return false
  }

  const user = computed(() => userState.value.user || null)

  return { user, isAuthenticated, loadUser, logout, login }
}
