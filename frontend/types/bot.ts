export enum BotStatus {
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  DEPRECATED = 'DEPRECATED',
}

export type BotStatuses = keyof typeof BotStatus

export type BotInfos = {
  id: string
  name: string
  description: string
  version: string
  status: BotStatuses
  lastUpdated: string
  slug: string
}
