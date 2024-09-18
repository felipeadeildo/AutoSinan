import type { BotExecution } from '~/types/bot'

export const useBotExecutions = (botSlug: string) => {
  const { status, data: botExecutions } = useFetch<BotExecution[]>(
    `/api/executions/${botSlug}`
  )

  return { status, botExecutions }
}
