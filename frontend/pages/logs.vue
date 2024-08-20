<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    middleware: 'auth',
    allowedRoles: ['user', 'admin'],
  })
</script>

<template>
  <div>
    Página onde serão mostrados os logs da aplicação (aplicar filtros, exportar,
    etc. etc.)
  </div>
</template>
