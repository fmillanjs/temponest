/**
 * Client-side API utilities
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function fetchApi<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new ApiError(
      data.message || `Request failed: ${response.statusText}`,
      response.status,
      data
    )
  }

  return response.json()
}

/**
 * Stream data from an API endpoint using Server-Sent Events
 */
export async function* streamApi(
  url: string,
  options?: RequestInit
): AsyncGenerator<string> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(
      `Stream failed: ${response.statusText}`,
      response.status
    )
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is not readable')
  }

  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      yield decoder.decode(value, { stream: true })
    }
  } finally {
    reader.releaseLock()
  }
}
