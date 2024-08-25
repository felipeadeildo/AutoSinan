<script setup lang="ts">
  const { path } = useRoute()
  const botSlug = computed(() =>
    path.includes('/bots/') ? path.split('/bots/')[1].split('/')[0] : ''
  )

  const logInOutItem = useNavigationLogInOutItem()

  const links = [
    [
      {
        label: 'Executar',
        icon: 'i-heroicons-home',
        to: `/bots/${botSlug.value}/run`,
      },
      {
        label: 'Configurações',
        icon: 'i-heroicons-wrench-screwdriver',
        to: `/bots/${botSlug.value}/settings`,
      },
      {
        label: 'LOGs',
        icon: 'i-heroicons-clipboard-document-list',
        to: `/bots/${botSlug.value}/logs`,
      },
    ],
    [
      {
        label: 'Início',
        icon: 'i-heroicons-home',
        to: '/',
      },
      logInOutItem,
    ],
  ]
</script>

<template>
  <UHorizontalNavigation
    :links="links"
    class="border-b border-gray-200 dark:border-gray-800"
  />

  <UContainer class="flex-1">
    <NuxtPage />
  </UContainer>

  <GlobalLoading />
  <UNotifications />
</template>
