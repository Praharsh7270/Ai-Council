"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, Send, AlertCircle, CheckCircle2, DollarSign, Clock } from "lucide-react"
import { useDemoRateLimit } from "@/hooks/use-demo-rate-limit"

interface DemoStage {
  stage: string
  message: string
  timestamp: number
}

export function DemoQueryInterface() {
  const [query, setQuery] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [stages, setStages] = useState<DemoStage[]>([])
  const [result, setResult] = useState<string | null>(null)
  const [costSavings, setCostSavings] = useState<{ council: number; single: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const { 
    remainingQueries, 
    isLimited, 
    consumeQuery, 
    getFormattedResetTime,
    checkAndResetIfExpired 
  } = useDemoRateLimit()

  const characterLimit = 200
  const charactersRemaining = characterLimit - query.length

  // Check if rate limit has expired on mount and periodically
  useEffect(() => {
    checkAndResetIfExpired()
    
    const interval = setInterval(() => {
      checkAndResetIfExpired()
    }, 10000) // Check every 10 seconds
    
    return () => clearInterval(interval)
  }, [checkAndResetIfExpired])

  const handleSubmit = async () => {
    if (query.trim().length === 0 || query.length > characterLimit) return
    if (isLimited) return

    setIsProcessing(true)
    setStages([])
    setResult(null)
    setCostSavings(null)
    setError(null)

    // Simulate demo processing with orchestration stages
    try {
      // Stage 1: Analysis
      await new Promise(resolve => setTimeout(resolve, 800))
      setStages(prev => [...prev, {
        stage: "Analysis",
        message: "Analyzing query complexity and intent...",
        timestamp: Date.now()
      }])

      // Stage 2: Decomposition
      await new Promise(resolve => setTimeout(resolve, 1000))
      setStages(prev => [...prev, {
        stage: "Decomposition",
        message: "Breaking down into 2 specialized subtasks...",
        timestamp: Date.now()
      }])

      // Stage 3: Routing
      await new Promise(resolve => setTimeout(resolve, 600))
      setStages(prev => [...prev, {
        stage: "Routing",
        message: "Assigning tasks to optimal models...",
        timestamp: Date.now()
      }])

      // Stage 4: Execution
      await new Promise(resolve => setTimeout(resolve, 1200))
      setStages(prev => [...prev, {
        stage: "Execution",
        message: "Processing 2 subtasks in parallel...",
        timestamp: Date.now()
      }])

      // Stage 5: Synthesis
      await new Promise(resolve => setTimeout(resolve, 800))
      setStages(prev => [...prev, {
        stage: "Synthesis",
        message: "Combining results into coherent response...",
        timestamp: Date.now()
      }])

      // Final result
      await new Promise(resolve => setTimeout(resolve, 400))
      setResult("This is a demo response showing how AI Council orchestrates multiple specialized models to provide high-quality answers efficiently. In production, this would be a real AI-generated response.")
      
      // Cost comparison
      setCostSavings({
        council: 0.0089,
        single: 0.0180
      })

      // Consume one query from rate limit
      consumeQuery()
    } catch (err) {
      setError("Demo processing failed. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <section className="py-20 sm:py-32 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Try It Now
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Experience AI Council's multi-agent orchestration with a live demo
          </p>
        </div>

        <div className="mx-auto max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Demo Query</span>
                <span className="text-sm font-normal text-muted-foreground">
                  {remainingQueries} {remainingQueries === 1 ? 'query' : 'queries'} remaining
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Query Input */}
              <div className="space-y-2">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question or describe a task... (max 200 characters)"
                  className="w-full min-h-[100px] rounded-lg border bg-background px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isProcessing || isLimited}
                  maxLength={characterLimit}
                />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className={charactersRemaining < 20 ? "text-orange-500" : ""}>
                    {charactersRemaining} characters remaining
                  </span>
                  {isLimited && (
                    <span className="text-orange-500 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      Demo limit reached
                    </span>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <Button
                onClick={handleSubmit}
                disabled={isProcessing || query.trim().length === 0 || query.length > characterLimit || isLimited}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Submit Query
                  </>
                )}
              </Button>

              {/* Rate Limit Message */}
              {isLimited && (
                <div className="rounded-lg bg-orange-500/10 border border-orange-500/20 p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-orange-500 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-orange-500">Demo Limit Reached</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        You've used all 3 demo queries. Your limit will reset in <span className="font-medium text-foreground">{getFormattedResetTime()}</span>.
                      </p>
                      <p className="text-sm text-muted-foreground mt-2">
                        Or register for a free account to submit unlimited queries with full orchestration capabilities.
                      </p>
                      <Button variant="outline" size="sm" className="mt-3">
                        Create Free Account
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4">
                  <div className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">{error}</span>
                  </div>
                </div>
              )}

              {/* Orchestration Stages */}
              {stages.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Orchestration Progress</h3>
                  <div className="space-y-2">
                    {stages.map((stage, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-3 rounded-lg border bg-card p-3 animate-in fade-in slide-in-from-left-2"
                      >
                        <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                        <div className="flex-1">
                          <div className="text-sm font-medium">{stage.stage}</div>
                          <div className="text-xs text-muted-foreground">{stage.message}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Result Display */}
              {result && (
                <div className="space-y-4">
                  <div className="rounded-lg border bg-card p-4">
                    <h3 className="text-sm font-medium mb-2">Response</h3>
                    <p className="text-sm text-muted-foreground">{result}</p>
                  </div>

                  {/* Cost Savings Comparison */}
                  {costSavings && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Card className="border-green-500/20 bg-green-500/5">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <DollarSign className="h-4 w-4 text-green-500" />
                            <span className="text-sm font-medium">AI Council Cost</span>
                          </div>
                          <div className="text-2xl font-bold text-green-500">
                            ${costSavings.council.toFixed(4)}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Multi-agent orchestration
                          </div>
                        </CardContent>
                      </Card>

                      <Card className="border-muted">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Single Model Cost</span>
                          </div>
                          <div className="text-2xl font-bold text-muted-foreground">
                            ${costSavings.single.toFixed(4)}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Traditional approach
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {costSavings && (
                    <div className="rounded-lg bg-primary/10 border border-primary/20 p-4 text-center">
                      <div className="text-sm font-medium text-primary">
                        💰 You saved {((1 - costSavings.council / costSavings.single) * 100).toFixed(0)}% with AI Council
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Plus faster response time through parallel execution
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Info Box */}
          <div className="mt-6 rounded-lg bg-muted/50 border p-4 text-center">
            <p className="text-sm text-muted-foreground">
              This is a demo with simulated orchestration. 
              <span className="font-medium text-foreground"> Register for free</span> to access real AI models and unlimited queries.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
