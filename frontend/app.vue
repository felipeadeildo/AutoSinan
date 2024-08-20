<script setup lang="ts">
  const { isAuthenticated } = useAuth()

  const links = [
    [
      { label: 'theme' },
      {
        label: 'Dashboard',
        icon: 'i-clarity-home-line',
        to: '/',
        labelClass: 'font-semibold',
      },
      {
        label: 'Logs',
        icon: 'i-clarity-list-line',
        to: '/logs',
      },
      {
        label: 'Configurações',
        icon: 'i-clarity-settings-line',
        to: '/settings',
      },
      {
        label: 'Sobre',
        icon: 'i-clarity-info-circle-line',
        to: '/about',
      },
      {
        label: isAuthenticated ? 'Sair' : 'Login',
        icon: 'i-clarity-login-line',
        to: isAuthenticated ? '/logout' : '/login',
      },
    ],
  ]

  const isDark = computed({
    get() {
      return colorMode.value === 'dark'
    },
    set() {
      colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
    },
  })

  const colorMode = useColorMode()
</script>

<template>
  <div class="grid grid-cols-12">
    <UVerticalNavigation :links="links" class="col-span-2">
      <template #default="{ link }">
        <ClientOnly v-if="link.label === 'theme'">
          <UButton
            :icon="
              isDark ? 'i-heroicons-moon-20-solid' : 'i-heroicons-sun-20-solid'
            "
            color="gray"
            variant="ghost"
            aria-label="Theme"
            @click="isDark = !isDark"
          />
          <template #fallback>
            <div class="w-8 h-8" />
          </template>
        </ClientOnly>
      </template>
    </UVerticalNavigation>
    <UContainer class="col-span-12 lg:col-span-10">
      <NuxtPage />
    </UContainer>
  </div>

  <UNotifications />
</template>
