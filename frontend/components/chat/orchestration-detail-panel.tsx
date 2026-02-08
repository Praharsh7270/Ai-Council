'use client';

import { useState } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { CouncilResponse } from '@/types/council';
import {
  Network,
  Zap,
  DollarSign,
  Clock,
  Target,
  GitBranch,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

interface OrchestrationDetailPanelProps {
  response: CouncilResponse;
}

export function OrchestrationDetailPanel({ response }: OrchestrationDetailPanelProps) {
  const [expandedItems, setExpandedItems] = useState<string[]>(['overview']);

  const orchestrationMetadata = response.orchestrationMetadata || {};
  const subtaskResults = response.subtaskResults || [];
  const modelsUsed = response.modelsUsed || [];

  // Calculate parallel efficiency
  const totalExecutionTime = response.executionTime;
  const sequentialTime = subtaskResults.reduce((sum, st) => sum + (st.executionTime || 0), 0);
  const parallelEfficiency = sequentialTime > 0 ? (sequentialTime / totalExecutionTime) * 100 : 0;

  return (
    <div className="border-t mt-6 pt-6">
      <Accordion
        type="multiple"
        value={expandedItems}
        onValueChange={setExpandedItems}
        className="space-y-2"
      >
        {/* Overview */}
        <AccordionItem value="overview" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4" />
              <span className="font-semibold">Orchestration Overview</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="space-y-4 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <GitBranch className="h-3 w-3" />
                  <span>Subtasks</span>
                </div>
                <div className="text-lg font-semibold">{subtaskResults.length}</div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Zap className="h-3 w-3" />
                  <span>Parallel Efficiency</span>
                </div>
                <div className="text-lg font-semibold">{parallelEfficiency.toFixed(0)}%</div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>Total Time</span>
                </div>
                <div className="text-lg font-semibold">{totalExecutionTime.toFixed(2)}s</div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <DollarSign className="h-3 w-3" />
                  <span>Total Cost</span>
                </div>
                <div className="text-lg font-semibold">${response.totalCost.toFixed(4)}</div>
              </div>
            </div>

            {/* Efficiency Explanation */}
            <div className="text-xs text-muted-foreground bg-muted p-3 rounded-lg">
              <strong>Parallel Efficiency:</strong> This shows how much faster the orchestration was
              compared to running all subtasks sequentially. Higher is better!
              {parallelEfficiency > 100 && (
                <span className="block mt-1">
                  🎉 Achieved {parallelEfficiency.toFixed(0)}% efficiency through parallel execution!
                </span>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Task Decomposition */}
        <AccordionItem value="decomposition" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              <span className="font-semibold">Task Decomposition</span>
              <Badge variant="secondary">{subtaskResults.length} subtasks</Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="space-y-3 pt-4">
            {subtaskResults.map((subtask, index) => (
              <div
                key={index}
                className="border rounded-lg p-3 space-y-2 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        Subtask {index + 1}
                      </Badge>
                      {subtask.taskType && (
                        <Badge variant="secondary" className="text-xs">
                          {subtask.taskType}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm">{subtask.content}</p>
                  </div>
                  {subtask.status === 'completed' ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-orange-500 flex-shrink-0" />
                  )}
                </div>

                {subtask.result && (
                  <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
                    {subtask.result.substring(0, 150)}
                    {subtask.result.length > 150 && '...'}
                  </div>
                )}
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>

        {/* Model Assignments */}
        <AccordionItem value="models" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              <span className="font-semibold">Model Assignments</span>
              <Badge variant="secondary">{modelsUsed.length} models</Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="space-y-3 pt-4">
            {subtaskResults.map((subtask, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="text-sm font-medium mb-1">Subtask {index + 1}</div>
                  <div className="text-xs text-muted-foreground">
                    {subtask.content.substring(0, 60)}...
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="default" className="mb-1">
                    {subtask.assignedModel || 'Unknown'}
                  </Badge>
                  {subtask.confidence !== undefined && (
                    <div className="text-xs text-muted-foreground">
                      {(subtask.confidence * 100).toFixed(0)}% confidence
                    </div>
                  )}
                </div>
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>

        {/* Cost Breakdown */}
        <AccordionItem value="cost" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              <span className="font-semibold">Cost Breakdown</span>
              <Badge variant="secondary">${response.totalCost.toFixed(4)}</Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="space-y-3 pt-4">
            {/* By Subtask */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-2">By Subtask</div>
              <div className="space-y-2">
                {subtaskResults.map((subtask, index) => {
                  const cost = subtask.cost || 0;
                  const percentage = response.totalCost > 0 ? (cost / response.totalCost) * 100 : 0;
                  return (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span>Subtask {index + 1}</span>
                        <span className="font-mono">${cost.toFixed(4)}</span>
                      </div>
                      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* By Model */}
            <div className="pt-3 border-t">
              <div className="text-xs font-medium text-muted-foreground mb-2">By Model</div>
              <div className="space-y-2">
                {modelsUsed.map((model, index) => {
                  // Calculate cost for this model (sum of all subtasks using this model)
                  const modelCost = subtaskResults
                    .filter((st) => st.assignedModel === model)
                    .reduce((sum, st) => sum + (st.cost || 0), 0);
                  const percentage = response.totalCost > 0 ? (modelCost / response.totalCost) * 100 : 0;
                  
                  return (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="truncate">{model}</span>
                        <span className="font-mono">${modelCost.toFixed(4)}</span>
                      </div>
                      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Execution Timeline */}
        <AccordionItem value="timeline" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <span className="font-semibold">Execution Timeline</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="space-y-3 pt-4">
            <div className="space-y-3">
              {subtaskResults.map((subtask, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    {index < subtaskResults.length - 1 && (
                      <div className="w-0.5 h-full bg-border my-1" style={{ minHeight: '20px' }} />
                    )}
                  </div>
                  <div className="flex-1 pb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Subtask {index + 1}</span>
                      <span className="text-xs text-muted-foreground">
                        {subtask.executionTime?.toFixed(2)}s
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {subtask.assignedModel || 'Unknown model'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
