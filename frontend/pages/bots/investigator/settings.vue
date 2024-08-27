<script lang="ts" setup>
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
    layout: 'bot',
  })

  const botSlug = 'investigator'
  const { botConfigurations, status } = useBotConfigurations(botSlug)
</script>

<template>
  <div class="h-screen flex flex-col justify-center items-center p-6">
    <h1 class="text-4xl font-extrabold mb-8 text-center">
      Configurações do Bot de Investigação
    </h1>

    <div v-if="status === 'pending'" class="mt-10">
      <LoadingState text="Carregando configurações..." />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
      <template v-for="config in botConfigurations" :key="config.key">
        <ConfigInput
          v-if="config.type === 'STRING' && !config.options"
          :config="config"
          :botSlug="botSlug"
        />

        <ConfigSelect
          v-else-if="config.options"
          :config="config"
          :botSlug="botSlug"
        />
      </template>
    </div>
  </div>
</template>
