// SSE consumer for backend `text/event-stream` endpoints.
//
// The backend emits one `event:` line followed by one `data:` line per record,
// terminated by a blank line. This helper reads chunks via fetch + ReadableStream,
// parses each complete record, and dispatches to the registered handler. It
// stops on `error` events and surfaces a thrown Error so call sites get the
// usual try/catch ergonomics.

export type SSEHandlers = Record<string, (data: string) => void | Promise<void>>

export interface ConsumeSSEOptions {
  body?: unknown
  signal?: AbortSignal
  onError?: (message: string) => void
}

export async function consumeSSE(
  url: string,
  handlers: SSEHandlers,
  options: ConsumeSSEOptions = {},
): Promise<void> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  })
  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new Error(text || `HTTP ${response.status}`)
  }
  if (!response.body) throw new Error('No stream body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const raw of lines) {
      const line = raw.replace(/\r$/, '')
      if (line === '') {
        currentEvent = ''
        continue
      }
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (currentEvent === 'error') {
          options.onError?.(data)
          throw new Error(data || 'stream error')
        }
        const handler = handlers[currentEvent]
        if (handler) await handler(data)
      }
    }
  }
}
