// Share simultaneous reads, then discard the promise so subsequent reads stay fresh.
export function createRequestDeduper() {
  const pending = new Map()
  return (key, request) => {
    if (pending.has(key)) return pending.get(key)
    const result = Promise.resolve().then(request).finally(() => pending.delete(key))
    pending.set(key, result)
    return result
  }
}
