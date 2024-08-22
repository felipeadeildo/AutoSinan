<script setup lang="ts">
  withDefaults(defineProps<{ text?: string }>(), {
    text: 'Carregando...',
  })
</script>

<template>
  <div class="flex justify-center items-center py-10">
    <UIcon
      name="i-heroicons-arrow-path-20-solid"
      size="lg"
      class="animate-spin"
    />
    <span class="ml-3 text-lg text-primary-500">{{ text }}</span>
  </div>
</template>
