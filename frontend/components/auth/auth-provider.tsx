'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/lib/auth-store'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { token, refreshUser } = useAuthStore()

  useEffect(() => {
    // Refresh user data on mount if token exists
    if (token) {
      refreshUser()
    }
  }, []) // Only run on mount

  useEffect(() => {
    // Set up token refresh interval (refresh 1 day before expiration)
    // JWT tokens expire in 7 days, so refresh every 6 days
    const refreshInterval = 6 * 24 * 60 * 60 * 1000 // 6 days in milliseconds

    if (token) {
      const intervalId = setInterval(() => {
        refreshUser()
      }, refreshInterval)

      return () => clearInterval(intervalId)
    }
  }, [token, refreshUser])

  return <>{children}</>
}
