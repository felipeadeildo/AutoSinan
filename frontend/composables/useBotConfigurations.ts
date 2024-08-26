import type { BotConfiguration } from '~/types/bot'

type Props = {
  bot: string
}

export const useBotConfigurations = ({ bot }: Props) => {
  const { status, data: botConfigurations } = useFetch<BotConfiguration[]>(
    `/api/configurations/${bot}`
  )

  return { status, botConfigurations }
}
