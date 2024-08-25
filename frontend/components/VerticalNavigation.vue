<script setup lang="ts">
  const logInOutItem = useNavigationLogInOutItem()

  const links = ref([
    [
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
      logInOutItem,
    ],
  ])
</script>

<template>
  <UVerticalNavigation
    :links="links"
    class="border-r-2 border-r-gray-900 rounded-r-lg h-full"
  />
</template>
