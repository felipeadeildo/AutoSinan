export default defineNuxtRouteMiddleware(async (to) => {
  const { loadUser, isAuthenticated } = useAuth()

  await loadUser()

  if (to.meta.requiresAuth && !isAuthenticated) {
    return navigateTo('/login')
  }

  const requiredRoles = to.meta.requiredRoles as string[] | undefined
  const { user } = useAuth()
  if (
    requiredRoles &&
    !requiredRoles.some((role) => user.value?.role.name === role)
  ) {
    return navigateTo('/login')
  }
})
