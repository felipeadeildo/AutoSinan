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

export enum ExecStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

export type ExecFile = {
  id: string
  filePath: string
  fileName: string
  fileMeta: Record<string, any> // Metadados do arquivo, pode ser um JSON genérico
}

export type LogEntry = {
  id: string
  timestamp: string
  message: string
  level: LogLevel
}

export enum LogLevel {
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  DEBUG = 'DEBUG',
}

export type BotExecution = {
  id: string
  bot: BotInfos
  startTime: string
  endTime?: string
  status: ExecStatus
  metadata: Record<string, any> // Metadados que podem ser armazenados como JSON
  // logs: LogEntry[] // Lista de logs associados a essa execução
  // files: ExecFile[] // Lista de arquivos associados à execução
}
