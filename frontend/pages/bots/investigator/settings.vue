<script lang="ts" setup>
  definePageMeta({
    requiresAuth: true,
    allowedRoles: ['user', 'admin'],
    layout: 'bot',
  })

  const { botConfigurations } = useBotConfigurations('investigator')
  const { updateConfiguration } = useBotConfigurationUpdate('investigator')
</script>

<template>
  <div class="h-screen flex justify-center items-center">
    <h1 class="text-4xl font-extrabold mb-6 text-center">
      Configurações do bot de investigação

      <div class="grid grid-cols-2 gap-3">
        <template v-for="config in botConfigurations" :key="config.key">
          <ConfigInput
            v-if="config.type === 'STRING' && !config.options"
            :config="config"
            @save="updateConfiguration"
          />

          <ConfigSelect
            v-else-if="config.options"
            :config="config"
            @save="updateConfiguration"
          />
        </template>
      </div>
    </h1>
  </div>
</template>
