<script lang="ts" setup>
  import type { BotInfos } from '~/types/bot'

  const { bot } = defineProps<{
    bot: BotInfos
  }>()

  const botStatusColor = computed(() => {
    switch (bot.status) {
      case 'ACTIVE':
        return 'green'
      case 'PAUSED':
        return 'yellow'
      case 'DEPRECATED':
        return 'red'
    }
  })

  const botStatusDescription = computed(() => {
    switch (bot.status) {
      case 'ACTIVE':
        return 'Pode ser utilizado sem problemas!'
      case 'PAUSED':
        return 'Este bot está desativado no momento.'
      case 'DEPRECATED':
        return 'Este bot foi descontinuado e não deve ser mais utilizado.'
    }
  })

  const botLastUpdated = computed(() => {
    return new Date(bot.lastUpdated).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  })
</script>

<template>
  <UCard
    :ui="{
      header: {
        padding: 'px-4 py-3 sm:px-5',
      },
      body: {
        padding: 'py-2 sm:py-3 sm:px-2',
      },
      footer: { padding: 'px-3 py-2 sm:px-5', base: 'text-end' },
    }"
  >
    <template #header>
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-semibold">{{ bot.name }}</h2>
        <UTooltip :text="botStatusDescription" :popper="{ arrow: true }">
          <UBadge :color="botStatusColor" variant="soft">
            {{ bot.status }}
          </UBadge>
        </UTooltip>
      </div>
    </template>

    <div class="px-4 py-2">
      <p class="text-sm">{{ bot.description }}</p>
      <p class="text-xs mt-1 text-end">Versão: {{ bot.version }}</p>
      <p class="text-xs text-end">Última Atualização: {{ botLastUpdated }}</p>
    </div>

    <template #footer>
      <UButton
        :to="`/bots/${bot.slug}`"
        icon="i-mdi-arrow-right"
        color="primary"
        size="sm"
      >
        Acessar
      </UButton>
    </template>
  </UCard>
</template>
