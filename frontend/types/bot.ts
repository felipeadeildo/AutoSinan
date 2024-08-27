export enum BotStatus {
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  DEPRECATED = 'DEPRECATED',
}

export type BotStatuses = keyof typeof BotStatus

export type BotInfos = {
  id: string
  name: string
  desc: string
  version: string
  status: BotStatuses
  updatedAt: string
  slug: string
}

export type BotConfiguration = {
  key: string
  value: string
  type: ConfigValueType
  name: string
  desc: string
  options: Array<{ key: string; value: string }>
}

export enum ConfigValueType {
  INT = 'INT',
  FLOAT = 'FLOAT',
  STRING = 'STRING',
  BOOLEAN = 'BOOLEAN',
}
