<script setup lang="ts">
  useHead({
    titleTemplate: (title) => (title ? `${title} | AutoSinan` : 'AutoSinan'),
  })
</script>

<template>
  <GlobalLoading />
  <div class="grid grid-cols-12 h-full min-h-screen">
    <!-- Sidebar Navigation -->
    <div class="col-span-2">
      <VerticalNavigation />
    </div>

    <!-- Main Content Area -->
    <div class="col-span-10 flex flex-col relative">
      <!-- Theme Toggle Button -->
      <ThemeToggle />

      <!-- Page Content -->
      <UContainer class="flex-1">
        <NuxtPage />
      </UContainer>
    </div>
  </div>

  <UNotifications />
</template>

<style>
  .page-enter-active,
  .page-leave-active {
    @apply transition-transform duration-300 ease-in-out;
  }

  .page-enter-from {
    @apply transform translate-y-full;
  }

  .page-leave-to {
    @apply transform -translate-y-full;
  }
</style>
