<script setup lang="ts">
  import type { BotInfos } from '~/types/bot'

  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
  })

  const session = useAuth()
  const { status, data: bots } = await useFetch<BotInfos[]>('/api/bots')
</script>

<template>
  <div>
    <WelcomeMessage :username="session.user.value?.name || ''" />

    <LoadingState v-if="status === 'pending'" />

    <ErrorState
      v-else-if="status === 'error'"
      title="Erro ao Carregar Bots"
      description="Ocorreu um erro ao carregar os bots. Por favor, tente novamente mais tarde."
    />

    <div v-else class="flex flex-wrap justify-center gap-4">
      <BotCard v-for="bot in bots" :key="bot.id" :bot="bot" />
    </div>
  </div>
</template>
