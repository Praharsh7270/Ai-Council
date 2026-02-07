"use client"

import { useState, useEffect } from "react"

interface DemoRateLimit {
  remainingQueries: number
  resetTime: number
  isLimited: boolean
}

const DEMO_LIMIT = 3
const RATE_LIMIT_WINDOW = 60 * 60 * 1000 // 1 hour in milliseconds
const STORAGE_KEY = "demo_rate_limit"

export function useDemoRateLimit() {
  const [rateLimit, setRateLimit] = useState<DemoRateLimit>({
    remainingQueries: DEMO_LIMIT,
    resetTime: Date.now() + RATE_LIMIT_WINDOW,
    isLimited: false
  })

  // Load rate limit from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return

    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as DemoRateLimit
        const now = Date.now()

        // Check if rate limit window has expired
        if (now >= parsed.resetTime) {
          // Reset the limit
          const newLimit = {
            remainingQueries: DEMO_LIMIT,
            resetTime: now + RATE_LIMIT_WINDOW,
            isLimited: false
          }
          setRateLimit(newLimit)
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newLimit))
        } else {
          // Use stored limit
          setRateLimit({
            ...parsed,
            isLimited: parsed.remainingQueries <= 0
          })
        }
      } catch (error) {
        console.error("Failed to parse rate limit data:", error)
      }
    }
  }, [])

  // Consume one query
  const consumeQuery = () => {
    setRateLimit(prev => {
      const newRemaining = Math.max(0, prev.remainingQueries - 1)
      const newLimit = {
        remainingQueries: newRemaining,
        resetTime: prev.resetTime,
        isLimited: newRemaining <= 0
      }

      // Persist to localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newLimit))
      }

      return newLimit
    })
  }

  // Get time until reset in seconds
  const getTimeUntilReset = (): number => {
    const now = Date.now()
    const diff = rateLimit.resetTime - now
    return Math.max(0, Math.ceil(diff / 1000))
  }

  // Format time until reset as human-readable string
  const getFormattedResetTime = (): string => {
    const seconds = getTimeUntilReset()
    
    if (seconds === 0) return "now"
    
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      const remainingMinutes = minutes % 60
      return `${hours}h ${remainingMinutes}m`
    } else if (minutes > 0) {
      const remainingSeconds = seconds % 60
      return `${minutes}m ${remainingSeconds}s`
    } else {
      return `${seconds}s`
    }
  }

  // Check if rate limit window has expired and reset if needed
  const checkAndResetIfExpired = () => {
    const now = Date.now()
    if (now >= rateLimit.resetTime) {
      const newLimit = {
        remainingQueries: DEMO_LIMIT,
        resetTime: now + RATE_LIMIT_WINDOW,
        isLimited: false
      }
      setRateLimit(newLimit)
      
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newLimit))
      }
      
      return true
    }
    return false
  }

  return {
    remainingQueries: rateLimit.remainingQueries,
    isLimited: rateLimit.isLimited,
    resetTime: rateLimit.resetTime,
    consumeQuery,
    getTimeUntilReset,
    getFormattedResetTime,
    checkAndResetIfExpired
  }
}
