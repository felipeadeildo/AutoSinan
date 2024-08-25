<script lang="ts" setup>
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
    layout: 'bot',
  })
</script>

<template>
  <div class="h-screen flex justify-center items-center">
    <h1 class="text-4xl font-extrabold mb-6 text-center">
      Logs do bot de investigação
    </h1>
  </div>
</template>
