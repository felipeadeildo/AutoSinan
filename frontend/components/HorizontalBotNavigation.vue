<script setup lang="ts">
  const route = useRoute()
  const botSlug = computed(() =>
    route.fullPath.includes('/bots/')
      ? route.fullPath.split('/bots/')[1].split('/')[0]
      : ''
  )

  const logInOutItem = useNavigationLogInOutItem()

  const links = computed(() => [
    [
      {
        label: 'Executar',
        icon: 'material-symbols-robot-2',
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
  ])
</script>

<template>
  <UHorizontalNavigation
    :links="links"
    class="border-b border-gray-200 dark:border-gray-800"
  />
</template>
