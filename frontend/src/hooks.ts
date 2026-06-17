import { useEffect, useState } from 'react'
import { PROGRESS_UPDATED_EVENT, readCompletedQuizSlugs } from './progression'

export function useAsyncData<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    setLoading(true)
    setError(null)

    loader()
      .then((value) => {
        if (!cancelled) {
          setData(value)
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : 'Unknown error')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, deps)

  return { data, error, loading }
}

export function useCompletedQuizSlugs() {
  const [completedQuizSlugs, setCompletedQuizSlugs] = useState<Set<string>>(() => readCompletedQuizSlugs())

  useEffect(() => {
    const refresh = () => {
      setCompletedQuizSlugs(readCompletedQuizSlugs())
    }

    window.addEventListener(PROGRESS_UPDATED_EVENT, refresh)
    window.addEventListener('storage', refresh)

    return () => {
      window.removeEventListener(PROGRESS_UPDATED_EVENT, refresh)
      window.removeEventListener('storage', refresh)
    }
  }, [])

  return completedQuizSlugs
}