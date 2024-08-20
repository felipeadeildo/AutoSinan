<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
  })

  const session = useAuth()
</script>

<template>
  <div>Olá, {{ session.user.value?.name }}</div>
</template>
