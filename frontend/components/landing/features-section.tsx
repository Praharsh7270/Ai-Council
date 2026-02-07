"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Network, Zap, DollarSign, Shield, BarChart3, Cpu } from "lucide-react"

const features = [
  {
    icon: Network,
    title: "Multi-Agent Orchestration",
    description: "Complex queries are automatically decomposed and distributed across specialized AI models for optimal results."
  },
  {
    icon: Zap,
    title: "Parallel Execution",
    description: "Independent tasks run simultaneously across multiple models, reducing total processing time by up to 3x."
  },
  {
    icon: DollarSign,
    title: "Cost Optimization",
    description: "Smart routing ensures each task uses the most cost-effective model, reducing expenses by up to 50%."
  },
  {
    icon: Shield,
    title: "Quality Assurance",
    description: "Built-in arbitration resolves conflicts between models, ensuring consistent and reliable outputs."
  },
  {
    icon: BarChart3,
    title: "Real-Time Insights",
    description: "Watch your query being processed in real-time with detailed orchestration visualization."
  },
  {
    icon: Cpu,
    title: "Model Specialization",
    description: "Each subtask is matched with the AI model best suited for that specific type of work."
  }
]

export function FeaturesSection() {
  return (
    <section className="py-20 sm:py-32">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Why AI Council?
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Harness the power of multiple AI models working together to deliver superior results
          </p>
        </div>
        
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Card key={index} className="transition-all hover:shadow-lg">
              <CardHeader>
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
