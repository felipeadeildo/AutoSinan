<script setup lang="ts">
  const { isAuthenticated } = useAuth()

  const colorMode = useColorMode()
  const isDark = computed({
    get() {
      return colorMode.value === 'dark'
    },
    set() {
      colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
    },
  })

  const links = ref([
    {
      label: 'AutoSinan',
      icon: 'i-clarity-shield-line',
      to: '#',
      labelClass: 'font-semibold cursor-default text-lg',
      clickable: false,
    },
    {
      label: 'Dashboard',
      icon: 'i-clarity-home-line',
      to: '/',
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
      label: computed(() => (isAuthenticated.value ? 'Sair' : 'Entrar')),
      icon: 'i-clarity-login-line',
      to: computed(() => (isAuthenticated.value ? '/logout' : '/login')),
    },
  ])
</script>

<template>
  <div class="grid grid-cols-12 h-full">
    <!-- Sidebar Navigation -->
    <UVerticalNavigation
      :links="links"
      class="col-span-2 border-r-2 border-r-gray-900 rounded-r-lg min-h-screen"
    />

    <!-- Main Content Area -->
    <div class="col-span-10 flex flex-col">
      <!-- Theme Toggle Button -->
      <ClientOnly>
        <UButton
          :icon="
            isDark ? 'i-heroicons-moon-20-solid' : 'i-heroicons-sun-20-solid'
          "
          variant="ghost"
          aria-label="Alterar tema"
          @click="isDark = !isDark"
          class="fixed bottom-4 right-4"
        />
      </ClientOnly>

      <UContainer>
        <NuxtPage />
      </UContainer>
    </div>
  </div>

  <UNotifications />
</template>
