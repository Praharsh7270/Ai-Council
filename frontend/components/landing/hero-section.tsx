"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-background to-muted/20 py-20 sm:py-32">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-8 inline-flex items-center rounded-full border bg-muted px-4 py-1.5 text-sm">
            <Sparkles className="mr-2 h-4 w-4 text-primary" />
            <span className="font-medium">Multi-Agent AI Orchestration</span>
          </div>
          
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
            Smarter AI Through
            <span className="block text-primary">Intelligent Collaboration</span>
          </h1>
          
          <p className="mx-auto mb-10 max-w-2xl text-lg text-muted-foreground sm:text-xl">
            AI Council breaks down complex queries and distributes them across specialized AI models, 
            delivering better results at lower costs through parallel processing and intelligent orchestration.
          </p>
          
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button size="lg" className="w-full sm:w-auto">
              Try Demo
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              Sign Up Free
            </Button>
          </div>
          
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
            <div className="rounded-lg border bg-card p-4">
              <div className="text-3xl font-bold text-primary">3x</div>
              <div className="text-sm text-muted-foreground">Faster Processing</div>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <div className="text-3xl font-bold text-primary">50%</div>
              <div className="text-sm text-muted-foreground">Lower Costs</div>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <div className="text-3xl font-bold text-primary">95%</div>
              <div className="text-sm text-muted-foreground">Accuracy Rate</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
