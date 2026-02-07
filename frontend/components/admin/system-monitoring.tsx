'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { MonitoringData } from '@/lib/admin-api'
import { Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface SystemMonitoringProps {
  monitoring: MonitoringData | null
}

export function SystemMonitoring({ monitoring }: SystemMonitoringProps) {
  if (!monitoring) {
    return null
  }

  const getHealthBadge = (status: 'healthy' | 'degraded' | 'down') => {
    switch (status) {
      case 'healthy':
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle className="h-3 w-3 mr-1" />
            Healthy
          </Badge>
        )
      case 'degraded':
        return (
          <Badge variant="default" className="bg-yellow-500">
            <AlertCircle className="h-3 w-3 mr-1" />
            Degraded
          </Badge>
        )
      case 'down':
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Down
          </Badge>
        )
    }
  }

  const getCircuitBreakerBadge = (state: 'open' | 'closed' | 'half-open') => {
    switch (state) {
      case 'closed':
        return (
          <Badge variant="default" className="bg-green-500">
            Closed
          </Badge>
        )
      case 'half-open':
        return (
          <Badge variant="default" className="bg-yellow-500">
            Half-Open
          </Badge>
        )
      case 'open':
        return (
          <Badge variant="destructive">
            Open
          </Badge>
        )
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Provider Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            AI Provider Health
          </CardTitle>
          <CardDescription>Status of cloud AI providers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Groq</p>
                <p className="text-sm text-gray-500">Ultra-fast inference</p>
              </div>
              {getHealthBadge(monitoring.providerHealth.groq)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Together.ai</p>
                <p className="text-sm text-gray-500">Diverse model selection</p>
              </div>
              {getHealthBadge(monitoring.providerHealth.together)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">OpenRouter</p>
                <p className="text-sm text-gray-500">Multi-provider access</p>
              </div>
              {getHealthBadge(monitoring.providerHealth.openrouter)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">HuggingFace</p>
                <p className="text-sm text-gray-500">Open models</p>
              </div>
              {getHealthBadge(monitoring.providerHealth.huggingface)}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Circuit Breaker States */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            Circuit Breaker States
          </CardTitle>
          <CardDescription>Failure protection status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Groq</p>
                <p className="text-sm text-gray-500">Failure threshold: 5</p>
              </div>
              {getCircuitBreakerBadge(monitoring.circuitBreakers.groq)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Together.ai</p>
                <p className="text-sm text-gray-500">Failure threshold: 5</p>
              </div>
              {getCircuitBreakerBadge(monitoring.circuitBreakers.together)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">OpenRouter</p>
                <p className="text-sm text-gray-500">Failure threshold: 5</p>
              </div>
              {getCircuitBreakerBadge(monitoring.circuitBreakers.openrouter)}
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">HuggingFace</p>
                <p className="text-sm text-gray-500">Failure threshold: 5</p>
              </div>
              {getCircuitBreakerBadge(monitoring.circuitBreakers.huggingface)}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
