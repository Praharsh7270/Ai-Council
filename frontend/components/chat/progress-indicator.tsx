'use client';

import { useEffect, useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Loader2,
  Search,
  GitBranch,
  Zap,
  Scale,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

interface ProgressIndicatorProps {
  stage: 'analysis' | 'routing' | 'execution' | 'arbitration' | 'synthesis' | 'complete';
  progress: number;
  completedSubtasks?: number;
  totalSubtasks?: number;
  activeModels?: string[];
}

const stageConfig = {
  analysis: {
    label: 'Analyzing',
    description: 'Understanding your query and breaking it down',
    icon: Search,
    color: 'text-blue-500',
  },
  routing: {
    label: 'Routing',
    description: 'Selecting the best AI models for each task',
    icon: GitBranch,
    color: 'text-purple-500',
  },
  execution: {
    label: 'Executing',
    description: 'Running tasks across multiple AI models',
    icon: Zap,
    color: 'text-yellow-500',
  },
  arbitration: {
    label: 'Arbitrating',
    description: 'Resolving conflicts and selecting best results',
    icon: Scale,
    color: 'text-orange-500',
  },
  synthesis: {
    label: 'Synthesizing',
    description: 'Combining results into a coherent response',
    icon: Sparkles,
    color: 'text-green-500',
  },
  complete: {
    label: 'Complete',
    description: 'Your response is ready!',
    icon: CheckCircle2,
    color: 'text-green-600',
  },
};

export function ProgressIndicator({
  stage,
  progress,
  completedSubtasks = 0,
  totalSubtasks = 0,
  activeModels = [],
}: ProgressIndicatorProps) {
  const [dots, setDots] = useState('');
  const config = stageConfig[stage];
  const Icon = config.icon;

  // Animated dots effect
  useEffect(() => {
    if (stage === 'complete') return;
    
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => clearInterval(interval);
  }, [stage]);

  return (
    <div className="space-y-4 p-6 bg-muted/30 rounded-lg border">
      {/* Stage Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`${config.color} ${stage !== 'complete' ? 'animate-pulse' : ''}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">
              {config.label}
              {stage !== 'complete' && <span className="inline-block w-6">{dots}</span>}
            </h3>
            <p className="text-sm text-muted-foreground">{config.description}</p>
          </div>
        </div>
        <Badge variant={stage === 'complete' ? 'default' : 'secondary'}>
          {progress}%
        </Badge>
      </div>

      {/* Progress Bar */}
      <Progress value={progress} className="h-2" />

      {/* Subtasks Progress */}
      {totalSubtasks > 0 && stage === 'execution' && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Subtasks completed</span>
          <span className="font-medium">
            {completedSubtasks} / {totalSubtasks}
          </span>
        </div>
      )}

      {/* Active Models */}
      {activeModels.length > 0 && stage === 'execution' && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Active Models:</div>
          <div className="flex flex-wrap gap-2">
            {activeModels.map((model, index) => (
              <div
                key={index}
                className="flex items-center gap-1.5 px-2 py-1 bg-background border rounded-md text-xs"
              >
                <Loader2 className="h-3 w-3 animate-spin text-primary" />
                <span>{model}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stage Indicators */}
      <div className="flex items-center justify-between pt-2 border-t">
        {Object.entries(stageConfig).map(([key, value], index) => {
          const isActive = key === stage;
          const isPast = Object.keys(stageConfig).indexOf(key) < Object.keys(stageConfig).indexOf(stage);
          const StageIcon = value.icon;

          return (
            <div
              key={key}
              className={`flex flex-col items-center gap-1 ${
                isActive ? 'opacity-100' : isPast ? 'opacity-60' : 'opacity-30'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : isPast
                    ? 'bg-primary/20 text-primary'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {isPast ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <StageIcon className="h-4 w-4" />
                )}
              </div>
              <span className="text-[10px] text-center hidden sm:block">
                {value.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
