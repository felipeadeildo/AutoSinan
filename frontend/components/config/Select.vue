<script setup lang="ts">
  import type { BotConfiguration } from '~/types/bot'

  const props = defineProps<{ config: BotConfiguration; botSlug: string }>()
  const value = ref(props.config.value)

  const { isUpdating, updateConfiguration } = useBotConfigurationUpdate(
    props.botSlug
  )

  const debouncedSave = useDebounce(async () => {
    await updateConfiguration({ ...props.config, value: value.value })
  }, 500)

  watch(value, debouncedSave)
</script>

<template>
  <UFormGroup
    :label="config.name"
    :ui="{
      help: 'text-gray-500 dark:text-gray-400 text-xs mt-0.5 flex items-center gap-1 justify-end',
    }"
  >
    <template #hint>
      <LoadingState v-if="isUpdating" text="Salvando..." text-class="text-sm" />
    </template>
    <template #default>
      <USelect
        v-model="value"
        :options="config.options"
        :disabled="isUpdating"
        option-attribute="key"
        placeholder="Selecione uma opção"
      />
    </template>
    <template #help>
      {{ config.desc }} <UIcon name="i-heroicons-information-circle" />
    </template>
  </UFormGroup>
</template>
