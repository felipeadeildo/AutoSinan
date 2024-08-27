import type { BotConfiguration } from '~/types/bot'

export const useBotConfigurationUpdate = (botSlug: string) => {
  const isUpdating = ref(false)

  const updateConfiguration = async (config: BotConfiguration) => {
    try {
      isUpdating.value = true

      await useFetch(`/api/configurations/${botSlug}`, {
        method: 'PUT',
        body: JSON.stringify(config),
      })
    } catch (error) {
      console.error(error)
    } finally {
      isUpdating.value = false
    }
  }

  return { isUpdating, updateConfiguration }
}
