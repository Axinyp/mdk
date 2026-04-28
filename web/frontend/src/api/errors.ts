type ApiErrorShape = {
  response?: { data?: { detail?: string } }
  message?: string
}

/** Extract a user-facing error message from an axios/network/Error value. */
export function errorMessage(err: unknown, fallback = '操作失败'): string {
  if (err && typeof err === 'object') {
    const e = err as ApiErrorShape
    return e.response?.data?.detail ?? e.message ?? fallback
  }
  if (typeof err === 'string') return err
  return fallback
}
