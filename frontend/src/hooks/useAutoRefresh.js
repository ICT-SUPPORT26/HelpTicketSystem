import { useState, useEffect, useRef, useCallback } from 'react'

export function useAutoRefresh(fetchFn, intervalMs = 30000) {
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const timerRef = useRef(null)
  const mountedRef = useRef(true)
  const fnRef = useRef(fetchFn)

  useEffect(() => { fnRef.current = fetchFn }, [fetchFn])

  const notifyUpdated = useCallback(() => {
    if (mountedRef.current) setLastUpdated(new Date())
  }, [])

  const refresh = useCallback(async () => {
    if (!mountedRef.current) return
    setIsRefreshing(true)
    try {
      await fnRef.current()
      if (mountedRef.current) setLastUpdated(new Date())
    } catch {}
    if (mountedRef.current) setIsRefreshing(false)
  }, [])

  useEffect(() => {
    mountedRef.current = true

    timerRef.current = setInterval(() => {
      if (!document.hidden) {
        fnRef.current()
          .then(() => { if (mountedRef.current) setLastUpdated(new Date()) })
          .catch(() => {})
      }
    }, intervalMs)

    const onVisibility = () => {
      if (!document.hidden && mountedRef.current) {
        fnRef.current()
          .then(() => { if (mountedRef.current) setLastUpdated(new Date()) })
          .catch(() => {})
      }
    }
    document.addEventListener('visibilitychange', onVisibility)

    return () => {
      mountedRef.current = false
      clearInterval(timerRef.current)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [intervalMs])

  return { lastUpdated, isRefreshing, refresh, notifyUpdated }
}
