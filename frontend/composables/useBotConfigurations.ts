import type { BotConfiguration } from '~/types/bot'


export const useBotConfigurations = (botSlug: string) => {
  const { status, data: botConfigurations } = useFetch<BotConfiguration[]>(
    `/api/configurations/${botSlug}`
  )

  return { status, botConfigurations }
}
