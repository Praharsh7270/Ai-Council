'use client';

import { useState, useEffect, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { councilApi } from '@/lib/council-api';
import type { ExecutionMode, CostEstimate, CouncilResponse } from '@/types/council';
import { Loader2, Send, HelpCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface EnhancedChatInputProps {
  onSubmit: (query: string, mode: ExecutionMode) => void;
  onResponseReceived?: (response: CouncilResponse) => void;
  onProgressUpdate?: (update: {
    stage?: 'analysis' | 'routing' | 'execution' | 'arbitration' | 'synthesis' | 'complete';
    progress?: number;
    completedSubtasks?: number;
    totalSubtasks?: number;
    activeModels?: string[];
  }) => void;
  disabled?: boolean;
}

export function EnhancedChatInput({
  onSubmit,
  onResponseReceived,
  onProgressUpdate,
  disabled = false,
}: EnhancedChatInputProps) {
  const [query, setQuery] = useState('');
  const [selectedMode, setSelectedMode] = useState<ExecutionMode>('balanced');
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [isLoadingEstimate, setIsLoadingEstimate] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toast } = useToast();

  const maxLength = 5000;
  const remainingChars = maxLength - query.length;

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 240; // ~10 lines
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [query]);

  // Fetch cost estimate when query changes (debounced)
  useEffect(() => {
    if (query.length < 10) {
      setCostEstimate(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoadingEstimate(true);
      try {
        const estimate = await councilApi.getCostEstimate(query);
        setCostEstimate(estimate);
      } catch (error) {
        console.error('Failed to fetch cost estimate:', error);
      } finally {
        setIsLoadingEstimate(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSubmit = async () => {
    if (!query.trim() || query.length > maxLength || isProcessing) {
      return;
    }

    setIsProcessing(true);
    onSubmit(query.trim(), selectedMode);

    try {
      // Submit the request
      const response = await councilApi.submitRequest(query.trim(), selectedMode);
      
      // Establish WebSocket connection for real-time updates
      const ws = new WebSocket(response.websocketUrl);
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        // Handle progress updates
        if (message.type === 'analysis_started' || message.type === 'analysis_complete') {
          onProgressUpdate?.({ stage: 'analysis', progress: 20 });
        } else if (message.type === 'routing_complete') {
          onProgressUpdate?.({ stage: 'routing', progress: 40 });
        } else if (message.type === 'execution_progress') {
          const completed = message.data.completedSubtasks || 0;
          const total = message.data.totalSubtasks || 1;
          onProgressUpdate?.({
            stage: 'execution',
            progress: 40 + (completed / total) * 30,
            completedSubtasks: completed,
            totalSubtasks: total,
            activeModels: message.data.activeModels || [],
          });
        } else if (message.type === 'arbitration_decision') {
          onProgressUpdate?.({ stage: 'arbitration', progress: 80 });
        } else if (message.type === 'synthesis_progress') {
          onProgressUpdate?.({ stage: 'synthesis', progress: 90 });
        } else if (message.type === 'final_response') {
          if (onResponseReceived) {
            onResponseReceived(message.data);
          }
          setIsProcessing(false);
          setQuery(''); // Clear input after successful submission
          ws.close();
        }
      };

      ws.onerror = () => {
        toast({
          title: 'Connection Error',
          description: 'Failed to establish real-time connection',
          variant: 'destructive',
        });
        setIsProcessing(false);
      };

    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit query. Please try again.',
        variant: 'destructive',
      });
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isValid = query.trim().length > 0 && query.length <= maxLength;

  return (
    <div className="space-y-4">
      {/* Main Input Area */}
      <div className="relative">
        <Textarea
          ref={textareaRef}
          placeholder="Ask AI Council anything... (Press Enter to send, Shift+Enter for new line)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="min-h-[72px] pr-12 resize-none"
          maxLength={maxLength}
          disabled={disabled || isProcessing}
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={!isValid || disabled || isProcessing}
          className="absolute right-2 bottom-2"
        >
          {isProcessing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Character Counter */}
      <div className="flex justify-between text-xs">
        <span className={remainingChars < 100 ? 'text-orange-500' : 'text-muted-foreground'}>
          {query.length} / {maxLength}
        </span>
      </div>

      {/* Execution Mode Selector */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Execution Mode</label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-xs">
                  Choose how AI Council processes your query:
                  <br />• Fast: Quick responses with minimal decomposition
                  <br />• Balanced: Best mix of speed, cost, and quality
                  <br />• Best Quality: Maximum accuracy with premium models
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="grid grid-cols-3 gap-2">
          {/* Fast Mode */}
          <button
            type="button"
            onClick={() => setSelectedMode('fast')}
            disabled={disabled || isProcessing}
            className={`p-3 border rounded-lg text-left transition-all text-sm ${
              selectedMode === 'fast'
                ? 'border-primary bg-primary/5 ring-2 ring-primary'
                : 'border-border hover:border-primary/50'
            } ${disabled || isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="font-semibold mb-1">⚡ Fast</div>
            {costEstimate && (
              <div className="text-xs text-muted-foreground">
                ${costEstimate.fast.toFixed(4)} • ~{costEstimate.estimatedTime.fast}s
              </div>
            )}
          </button>

          {/* Balanced Mode */}
          <button
            type="button"
            onClick={() => setSelectedMode('balanced')}
            disabled={disabled || isProcessing}
            className={`p-3 border rounded-lg text-left transition-all text-sm ${
              selectedMode === 'balanced'
                ? 'border-primary bg-primary/5 ring-2 ring-primary'
                : 'border-border hover:border-primary/50'
            } ${disabled || isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="font-semibold mb-1">⚖️ Balanced</div>
            {costEstimate && (
              <div className="text-xs text-muted-foreground">
                ${costEstimate.balanced.toFixed(4)} • ~{costEstimate.estimatedTime.balanced}s
              </div>
            )}
          </button>

          {/* Best Quality Mode */}
          <button
            type="button"
            onClick={() => setSelectedMode('best_quality')}
            disabled={disabled || isProcessing}
            className={`p-3 border rounded-lg text-left transition-all text-sm ${
              selectedMode === 'best_quality'
                ? 'border-primary bg-primary/5 ring-2 ring-primary'
                : 'border-border hover:border-primary/50'
            } ${disabled || isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="font-semibold mb-1">💎 Best</div>
            {costEstimate && (
              <div className="text-xs text-muted-foreground">
                ${costEstimate.bestQuality.toFixed(4)} • ~{costEstimate.estimatedTime.bestQuality}s
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Cost Estimate Loading */}
      {isLoadingEstimate && query.length >= 10 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Calculating estimates...</span>
        </div>
      )}
    </div>
  );
}
