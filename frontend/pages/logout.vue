<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
  })

  const session = useAuth()

  onMounted(() =>
    setTimeout(async () => {
      await session.logout()
      await navigateTo('/login')
    }, 2000)
  )
</script>

<template>
  <UAlert
    icon="i-pepicons-pop-arrows-spin-circle"
    color="blue"
    title="Saindo..."
    variant="soft"
    :ui="{
      icon: { base: 'flex-shrink-0 w-5 h-5 animate-spin' },
    }"
  />
</template>
