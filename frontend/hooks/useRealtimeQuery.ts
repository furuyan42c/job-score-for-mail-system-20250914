/**
 * T070: リアルタイム機能統合 - TDD Implementation
 * Real-time database change notifications using Supabase
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import { RealtimeChannel, RealtimePostgresChangesPayload } from '@supabase/supabase-js'

// Types for real-time events
export type RealtimeEvent = 'INSERT' | 'UPDATE' | 'DELETE'

export interface UseRealtimeQueryOptions {
  table: string
  select?: string
  filter?: Record<string, any>
  enabled?: boolean
  onInsert?: (payload: any) => void
  onUpdate?: (payload: any) => void
  onDelete?: (payload: any) => void
  onError?: (error: Error) => void
}

export interface UseRealtimeQueryResult<T = any> {
  data: T[] | null
  loading: boolean
  error: string | null
  isSubscribed: boolean
  refetch: () => Promise<void>
  stats: {
    inserts: number
    updates: number
    deletes: number
    lastUpdate: Date | null
  }
}

/**
 * Custom hook for real-time Supabase queries with automatic updates
 */
export function useRealtimeQuery<T = any>({
  table,
  select = '*',
  filter = {},
  enabled = true,
  onInsert,
  onUpdate,
  onDelete,
  onError
}: UseRealtimeQueryOptions): UseRealtimeQueryResult<T> {
  const [data, setData] = useState<T[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubscribed, setIsSubscribed] = useState(false)

  // Statistics tracking
  const [stats, setStats] = useState({
    inserts: 0,
    updates: 0,
    deletes: 0,
    lastUpdate: null as Date | null
  })

  const channelRef = useRef<RealtimeChannel | null>(null)

  // Build query with filters
  const buildQuery = useCallback(() => {
    let query = supabase.from(table).select(select)

    // Apply filters
    Object.entries(filter).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query = query.eq(key, value)
      }
    })

    return query
  }, [table, select, filter])

  // Fetch initial data
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const { data: result, error: err } = await buildQuery()

      if (err) {
        throw new Error(err.message)
      }

      setData(result as T[])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data'
      setError(errorMessage)
      if (onError) {
        onError(err as Error)
      }
    } finally {
      setLoading(false)
    }
  }, [buildQuery, onError])

  // Handle real-time INSERT events
  const handleInsert = useCallback((payload: RealtimePostgresChangesPayload<T>) => {
    console.log('Real-time INSERT detected:', payload)

    setData(current => {
      if (!current) return [payload.new as T]

      // Check if item already exists (prevent duplicates)
      const exists = current.some((item: any) => {
        const primaryKey = Object.keys(payload.new)[0]
        return item[primaryKey] === payload.new[primaryKey]
      })

      if (exists) return current

      return [...current, payload.new as T]
    })

    setStats(prev => ({
      ...prev,
      inserts: prev.inserts + 1,
      lastUpdate: new Date()
    }))

    if (onInsert) {
      onInsert(payload.new)
    }
  }, [onInsert])

  // Handle real-time UPDATE events
  const handleUpdate = useCallback((payload: RealtimePostgresChangesPayload<T>) => {
    console.log('Real-time UPDATE detected:', payload)

    setData(current => {
      if (!current) return null

      return current.map((item: any) => {
        const primaryKey = Object.keys(payload.new)[0]
        if (item[primaryKey] === payload.new[primaryKey]) {
          return payload.new as T
        }
        return item
      })
    })

    setStats(prev => ({
      ...prev,
      updates: prev.updates + 1,
      lastUpdate: new Date()
    }))

    if (onUpdate) {
      onUpdate(payload.new)
    }
  }, [onUpdate])

  // Handle real-time DELETE events
  const handleDelete = useCallback((payload: RealtimePostgresChangesPayload<T>) => {
    console.log('Real-time DELETE detected:', payload)

    setData(current => {
      if (!current) return null

      return current.filter((item: any) => {
        const primaryKey = Object.keys(payload.old)[0]
        return item[primaryKey] !== payload.old[primaryKey]
      })
    })

    setStats(prev => ({
      ...prev,
      deletes: prev.deletes + 1,
      lastUpdate: new Date()
    }))

    if (onDelete) {
      onDelete(payload.old)
    }
  }, [onDelete])

  // Setup real-time subscription
  useEffect(() => {
    if (!enabled) {
      return
    }

    // Initial data fetch
    fetchData()

    // Setup real-time subscription
    const setupSubscription = async () => {
      try {
        // Create unique channel name
        const channelName = `realtime-${table}-${Date.now()}`

        // Create channel and setup listeners
        const channel = supabase
          .channel(channelName)
          .on(
            'postgres_changes',
            {
              event: 'INSERT',
              schema: 'public',
              table: table
            },
            handleInsert
          )
          .on(
            'postgres_changes',
            {
              event: 'UPDATE',
              schema: 'public',
              table: table
            },
            handleUpdate
          )
          .on(
            'postgres_changes',
            {
              event: 'DELETE',
              schema: 'public',
              table: table
            },
            handleDelete
          )
          .subscribe((status) => {
            console.log(`Subscription status for ${table}:`, status)
            setIsSubscribed(status === 'SUBSCRIBED')

            if (status === 'SUBSCRIBED') {
              console.log(`✅ Real-time subscription active for table: ${table}`)
            } else if (status === 'CHANNEL_ERROR') {
              const error = new Error(`Failed to subscribe to ${table}`)
              setError(error.message)
              if (onError) {
                onError(error)
              }
            }
          })

        channelRef.current = channel

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to setup subscription'
        setError(errorMessage)
        setIsSubscribed(false)

        if (onError) {
          onError(err as Error)
        }
      }
    }

    setupSubscription()

    // Cleanup subscription on unmount or when dependencies change
    return () => {
      if (channelRef.current) {
        console.log(`Unsubscribing from real-time updates for ${table}`)
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
        setIsSubscribed(false)
      }
    }
  }, [enabled, table, fetchData, handleInsert, handleUpdate, handleDelete, onError])

  // Manual refetch function
  const refetch = useCallback(async () => {
    await fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    isSubscribed,
    refetch,
    stats
  }
}

/**
 * Hook for monitoring specific row changes in real-time
 */
export function useRealtimeRow<T = any>({
  table,
  id,
  primaryKey = 'id',
  enabled = true,
  onUpdate,
  onDelete,
  onError
}: {
  table: string
  id: any
  primaryKey?: string
  enabled?: boolean
  onUpdate?: (data: T) => void
  onDelete?: () => void
  onError?: (error: Error) => void
}): {
  data: T | null
  loading: boolean
  error: string | null
  isSubscribed: boolean
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubscribed, setIsSubscribed] = useState(false)

  const channelRef = useRef<RealtimeChannel | null>(null)

  useEffect(() => {
    if (!enabled || !id) {
      return
    }

    // Fetch initial row data
    const fetchRow = async () => {
      setLoading(true)
      setError(null)

      try {
        const { data: result, error: err } = await supabase
          .from(table)
          .select('*')
          .eq(primaryKey, id)
          .single()

        if (err) {
          throw new Error(err.message)
        }

        setData(result as T)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch row'
        setError(errorMessage)
        if (onError) {
          onError(err as Error)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchRow()

    // Setup real-time subscription for this specific row
    const channel = supabase
      .channel(`row-${table}-${id}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: table,
          filter: `${primaryKey}=eq.${id}`
        },
        (payload: RealtimePostgresChangesPayload<T>) => {
          console.log(`Row UPDATE detected for ${table}:${id}`, payload)
          setData(payload.new as T)
          if (onUpdate) {
            onUpdate(payload.new as T)
          }
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'DELETE',
          schema: 'public',
          table: table,
          filter: `${primaryKey}=eq.${id}`
        },
        (payload: RealtimePostgresChangesPayload<T>) => {
          console.log(`Row DELETE detected for ${table}:${id}`, payload)
          setData(null)
          if (onDelete) {
            onDelete()
          }
        }
      )
      .subscribe((status) => {
        console.log(`Row subscription status for ${table}:${id}:`, status)
        setIsSubscribed(status === 'SUBSCRIBED')
      })

    channelRef.current = channel

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
        setIsSubscribed(false)
      }
    }
  }, [enabled, table, id, primaryKey, onUpdate, onDelete, onError])

  return {
    data,
    loading,
    error,
    isSubscribed
  }
}