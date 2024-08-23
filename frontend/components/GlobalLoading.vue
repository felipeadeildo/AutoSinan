<script setup lang="ts">
  const isRouteLoading = useIsRouteLoading()
</script>

<template>
  <UModal v-model="isRouteLoading" :overlay="false">
    <LoadingState text="Carregando página..." />
  </UModal>
</template>
