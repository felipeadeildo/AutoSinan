// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  compatibilityDate: '2024-08-19',
  routeRules: {
    '/backend/**': {
      proxy:
        process.env.NODE_ENV === 'development'
          ? 'http://127.0.0.1:8000/**'
          : '/api/**',
    },
    '/docs': {
      proxy: 'http://127.0.0.1:8000/docs',
    },
    '/openapi.json': {
      proxy: 'http://127.0.0.1:8000/openapi.json',
    },
  },
})
