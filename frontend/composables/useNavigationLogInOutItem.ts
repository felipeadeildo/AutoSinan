import type {
  HorizontalNavigationLink,
  VerticalNavigationLink,
} from '#ui/types'

export const useNavigationLogInOutItem = ():
  | VerticalNavigationLink
  | HorizontalNavigationLink => {
  const { isAuthenticated } = useAuth()

  return {
    // @ts-ignore
    label: computed(() => (isAuthenticated.value ? 'Sair' : 'Entrar')),
    icon: 'i-clarity-login-line',
    // @ts-ignore
    to: computed(() => (isAuthenticated.value ? '/logout' : '/login')),
  }
}
