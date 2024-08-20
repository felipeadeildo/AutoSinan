<script setup lang="ts">
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
  })
</script>

<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-2xl font-bold">Logs</h1>
    <p>
      Esta página está em desenvolvimento e futuramente ter funcionalidades
      para:
    </p>
    <ul class="list-disc list-inside">
      <li>Filtrar logs por tipo, data e hora</li>
      <li>Exportar logs em formato CSV</li>
      <li>Verificar a quantidade de logs por tipo</li>
    </ul>
  </div>
</template>
