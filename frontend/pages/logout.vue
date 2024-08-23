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
    }, 1500)
  )
</script>

<template>
  <div class="flex justify-center items-center h-screen">
    <LoadingState text="Saindo..." />
  </div>
</template>
