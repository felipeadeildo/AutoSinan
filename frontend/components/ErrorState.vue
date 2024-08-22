<script setup lang="ts">
  withDefaults(defineProps<{ title?: string; description?: string }>(), {
    title: 'Erro',
    description: 'Ocorreu um erro. Por favor, tente novamente mais tarde.',
  })
</script>

<template>
  <div class="flex justify-center py-10">
    <UAlert
      icon="i-heroicons-x-circle"
      color="red"
      variant="soft"
      :title="title"
      :description="description"
    />
  </div>
</template>
