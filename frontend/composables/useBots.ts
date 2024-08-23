import type { AsyncDataRequestStatus } from '#app'
import type { BotInfos } from '~/types/bot'

export const useBots = (): {
  status: Ref<AsyncDataRequestStatus>
  bots: Ref<BotInfos[] | null>
} => {
  const { status, data: bots } = useFetch<BotInfos[]>('/api/bots')

  return { status, bots }
}
