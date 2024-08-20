<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    middleware: 'auth',
    allowedRoles: ['user', 'admin'],
  })
</script>

<template>
  <div>
    Página de configurações (geralmente, aqui é onde estarão todas as
    configurações de variáveis dos Bots)
  </div>
</template>
