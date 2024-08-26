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

export type BotConfiguration = {
  id: string
  key: string
  value: string
  type: ConfigValueType
}

export enum ConfigValueType {
  INT = 'INT',
  FLOAT = 'FLOAT',
  STRING = 'STRING',
  BOOLEAN = 'BOOLEAN',
}
