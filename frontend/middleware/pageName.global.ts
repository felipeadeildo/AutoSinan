export default defineNuxtRouteMiddleware(async (to) => {
  const name = to.name?.toString() || 'index'

  const namedPages = Object.keys(PAGE_NAMES)

  if (!name || !namedPages.includes(name)) return

  useHead({
    title: PAGE_NAMES[name as keyof typeof PAGE_NAMES],
    titleTemplate: (title) => (title ? `${title} | AutoSinan` : 'AutoSinan'),
  })
})
