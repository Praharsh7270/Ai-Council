"use client"

import { Card, CardContent } from "@/components/ui/card"
import { FileText, GitBranch, Cpu, Layers } from "lucide-react"

const steps = [
  {
    icon: FileText,
    title: "1. Analysis",
    description: "Your query is analyzed to understand complexity and intent"
  },
  {
    icon: GitBranch,
    title: "2. Decomposition",
    description: "Complex tasks are broken down into manageable subtasks"
  },
  {
    icon: Cpu,
    title: "3. Parallel Execution",
    description: "Subtasks are routed to specialized models and processed simultaneously"
  },
  {
    icon: Layers,
    title: "4. Synthesis",
    description: "Individual results are combined into a coherent final response"
  }
]

export function HowItWorksSection() {
  return (
    <section className="bg-muted/30 py-20 sm:py-32">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Four simple steps to smarter AI responses
          </p>
        </div>
        
        <div className="mx-auto max-w-5xl">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <Card className="h-full transition-all hover:shadow-lg">
                  <CardContent className="pt-6">
                    <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                      <step.icon className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="mb-2 text-xl font-semibold">{step.title}</h3>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </CardContent>
                </Card>
                {index < steps.length - 1 && (
                  <div className="absolute right-0 top-1/2 hidden -translate-y-1/2 translate-x-1/2 lg:block">
                    <div className="h-0.5 w-8 bg-primary/30"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-16 rounded-lg border bg-card p-8">
            <div className="flex flex-col items-center gap-6 md:flex-row">
              <div className="flex-shrink-0">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                  <Layers className="h-10 w-10 text-primary" />
                </div>
              </div>
              <div className="flex-1 text-center md:text-left">
                <h3 className="mb-2 text-2xl font-bold">See It In Action</h3>
                <p className="text-muted-foreground">
                  Watch real-time orchestration as your query flows through analysis, decomposition, 
                  parallel execution, and synthesis. Every step is transparent and trackable.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
