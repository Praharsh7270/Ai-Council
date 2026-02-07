"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { FileText, GitBranch, Cpu, Layers, CheckCircle2 } from "lucide-react"

type Stage = "idle" | "analysis" | "decomposition" | "execution" | "synthesis" | "complete"

const stages = [
  { id: "analysis", label: "Analysis", icon: FileText, color: "text-blue-500" },
  { id: "decomposition", label: "Decomposition", icon: GitBranch, color: "text-purple-500" },
  { id: "execution", label: "Parallel Execution", icon: Cpu, color: "text-green-500" },
  { id: "synthesis", label: "Synthesis", icon: Layers, color: "text-orange-500" },
]

const subtasks = [
  { id: 1, label: "Research Task", model: "Llama 3 70B" },
  { id: 2, label: "Reasoning Task", model: "Mixtral 8x7B" },
  { id: 3, label: "Code Generation", model: "GPT-4 Turbo" },
]

export function OrchestrationVisualization() {
  const [currentStage, setCurrentStage] = useState<Stage>("idle")
  const [completedSubtasks, setCompletedSubtasks] = useState<number[]>([])
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (!isAnimating) return

    const sequence = async () => {
      // Analysis
      setCurrentStage("analysis")
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Decomposition
      setCurrentStage("decomposition")
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Execution (parallel)
      setCurrentStage("execution")
      for (let i = 0; i < subtasks.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 800))
        setCompletedSubtasks(prev => [...prev, subtasks[i].id])
      }
      
      // Synthesis
      setCurrentStage("synthesis")
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Complete
      setCurrentStage("complete")
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Reset
      setCurrentStage("idle")
      setCompletedSubtasks([])
      setIsAnimating(false)
    }

    sequence()
  }, [isAnimating])

  const startAnimation = () => {
    if (!isAnimating) {
      setCurrentStage("idle")
      setCompletedSubtasks([])
      setIsAnimating(true)
    }
  }

  return (
    <section className="py-20 sm:py-32">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Watch Orchestration In Action
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            See how AI Council intelligently distributes work across multiple specialized models
          </p>
        </div>
        
        <div className="mx-auto max-w-5xl">
          <Card className="overflow-hidden">
            <CardContent className="p-8">
              {/* Stage Progress */}
              <div className="mb-8 flex items-center justify-between">
                {stages.map((stage, index) => (
                  <div key={stage.id} className="flex items-center">
                    <div className={`flex flex-col items-center ${
                      currentStage === stage.id ? "scale-110" : ""
                    } transition-transform duration-300`}>
                      <div className={`mb-2 flex h-12 w-12 items-center justify-center rounded-full ${
                        currentStage === stage.id 
                          ? "bg-primary text-primary-foreground animate-pulse" 
                          : stages.findIndex(s => s.id === currentStage) > index || currentStage === "complete"
                          ? "bg-primary/20 text-primary"
                          : "bg-muted text-muted-foreground"
                      }`}>
                        <stage.icon className="h-6 w-6" />
                      </div>
                      <span className={`text-xs font-medium ${
                        currentStage === stage.id ? stage.color : "text-muted-foreground"
                      }`}>
                        {stage.label}
                      </span>
                    </div>
                    {index < stages.length - 1 && (
                      <div className={`mx-4 h-0.5 w-12 ${
                        stages.findIndex(s => s.id === currentStage) > index || currentStage === "complete"
                          ? "bg-primary"
                          : "bg-muted"
                      } transition-colors duration-300`}></div>
                    )}
                  </div>
                ))}
              </div>

              {/* Visualization Area */}
              <div className="min-h-[300px] rounded-lg border-2 border-dashed bg-muted/30 p-6">
                {currentStage === "idle" && (
                  <div className="flex h-full items-center justify-center">
                    <button
                      onClick={startAnimation}
                      className="rounded-lg bg-primary px-6 py-3 text-primary-foreground hover:bg-primary/90 transition-colors"
                    >
                      Start Demo
                    </button>
                  </div>
                )}

                {currentStage === "analysis" && (
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <FileText className="h-16 w-16 text-blue-500 animate-pulse" />
                    <p className="text-center text-lg font-medium">
                      Analyzing query complexity and intent...
                    </p>
                  </div>
                )}

                {currentStage === "decomposition" && (
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <GitBranch className="h-16 w-16 text-purple-500 animate-pulse" />
                    <p className="text-center text-lg font-medium">
                      Breaking down into {subtasks.length} specialized subtasks...
                    </p>
                  </div>
                )}

                {currentStage === "execution" && (
                  <div className="space-y-4">
                    <p className="text-center text-lg font-medium mb-6">
                      Processing subtasks in parallel...
                    </p>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                      {subtasks.map((task) => (
                        <div
                          key={task.id}
                          className={`rounded-lg border p-4 transition-all ${
                            completedSubtasks.includes(task.id)
                              ? "border-green-500 bg-green-500/10"
                              : "border-muted bg-card animate-pulse"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">{task.label}</span>
                            {completedSubtasks.includes(task.id) && (
                              <CheckCircle2 className="h-5 w-5 text-green-500" />
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">{task.model}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {currentStage === "synthesis" && (
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <Layers className="h-16 w-16 text-orange-500 animate-pulse" />
                    <p className="text-center text-lg font-medium">
                      Combining results into coherent response...
                    </p>
                  </div>
                )}

                {currentStage === "complete" && (
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <CheckCircle2 className="h-16 w-16 text-green-500" />
                    <p className="text-center text-lg font-medium text-green-500">
                      Orchestration Complete!
                    </p>
                    <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-primary">2.3s</div>
                        <div className="text-xs text-muted-foreground">Total Time</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-primary">$0.012</div>
                        <div className="text-xs text-muted-foreground">Total Cost</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-primary">3</div>
                        <div className="text-xs text-muted-foreground">Models Used</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Benefits */}
              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-muted/50 p-4 text-center">
                  <div className="text-sm font-medium text-primary">Parallel Processing</div>
                  <div className="text-xs text-muted-foreground">3x faster than sequential</div>
                </div>
                <div className="rounded-lg bg-muted/50 p-4 text-center">
                  <div className="text-sm font-medium text-primary">Cost Optimized</div>
                  <div className="text-xs text-muted-foreground">50% cheaper than single model</div>
                </div>
                <div className="rounded-lg bg-muted/50 p-4 text-center">
                  <div className="text-sm font-medium text-primary">Specialized Models</div>
                  <div className="text-xs text-muted-foreground">Best model for each task</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}
