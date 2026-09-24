export const QUERY_KEYS = {
  sessions: (userId: string) => ['sessions', userId] as const,
  chatHistory: (sessionId: string) => ['chatHistory', sessionId] as const,
  ingestJob: (jobId: string) => ['ingestJob', jobId] as const,
}
