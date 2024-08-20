export default defineNuxtRouteMiddleware(async (to) => {
  const { loadUser, isAuthenticated } = useAuth()

  const noPermissionState = useState<boolean>('no-permission', () => false)

  await loadUser()

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    noPermissionState.value = true
    return navigateTo('/login')
  }

  const allowedRoles = to.meta.allowedRoles as string[] | undefined
  const { user } = useAuth()
  if (
    allowedRoles &&
    !allowedRoles.some((role) => user.value?.role.name === role)
  ) {
    noPermissionState.value = true
    return navigateTo('/login')
  }
})
