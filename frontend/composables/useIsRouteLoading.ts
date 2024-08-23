export const useIsRouteLoading = () => {
  const isRouteLoading = ref(false)
  const router = useRouter()

  router.beforeEach((to, from, next) => {
    isRouteLoading.value = true
    next()
  })

  router.afterEach(() => {
    isRouteLoading.value = false
  })

  return isRouteLoading
}
