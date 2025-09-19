/**
 * Shared logging utilities for Edge Functions
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

export class Logger {
  private functionName: string

  constructor(functionName: string) {
    this.functionName = functionName
  }

  private log(level: LogLevel, message: string, data?: any) {
    const timestamp = new Date().toISOString()
    const logEntry = {
      timestamp,
      level,
      function: this.functionName,
      message,
      ...(data && { data }),
    }
    console.log(JSON.stringify(logEntry))
  }

  debug(message: string, data?: any) {
    this.log(LogLevel.DEBUG, message, data)
  }

  info(message: string, data?: any) {
    this.log(LogLevel.INFO, message, data)
  }

  warn(message: string, data?: any) {
    this.log(LogLevel.WARN, message, data)
  }

  error(message: string, data?: any) {
    this.log(LogLevel.ERROR, message, data)
  }
}