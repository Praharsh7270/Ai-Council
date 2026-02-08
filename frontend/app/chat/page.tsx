'use client';

import { useState, useRef } from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout';
import { EnhancedChatInput } from '@/components/chat/enhanced-chat-input';
import { ResponsePanel } from '@/components/chat/response-panel';
import { AnalyticsPreview } from '@/components/chat/analytics-preview';
import { ChatHistorySidebar } from '@/components/chat/chat-history-sidebar';
import { ProgressIndicator } from '@/components/chat/progress-indicator';
import { KeyboardShortcutsDialog } from '@/components/chat/keyboard-shortcuts-dialog';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { CouncilResponse } from '@/types/council';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ProgressState {
  stage: 'analysis' | 'routing' | 'execution' | 'arbitration' | 'synthesis' | 'complete';
  progress: number;
  completedSubtasks: number;
  totalSubtasks: number;
  activeModels: string[];
}

function ResponsePanelSkeleton() {
  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between p-4 border-b">
        <Skeleton className="h-6 w-24" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-8 w-8 rounded" />
        </div>
      </div>

      {/* Content Skeleton */}
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-4">
          {/* Response Content Skeleton */}
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[95%]" />
            <Skeleton className="h-4 w-[90%]" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[85%]" />
          </div>

          <div className="space-y-3 mt-6">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[92%]" />
            <Skeleton className="h-4 w-[88%]" />
          </div>

          {/* Code Block Skeleton */}
          <div className="mt-6">
            <Skeleton className="h-32 w-full rounded-lg" />
          </div>

          <div className="space-y-3 mt-6">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[90%]" />
            <Skeleton className="h-4 w-[95%]" />
            <Skeleton className="h-4 w-[85%]" />
          </div>

          {/* Metadata Skeleton */}
          <div className="mt-8 pt-6 border-t grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <Skeleton className="h-3 w-20 mb-2" />
                <Skeleton className="h-6 w-16" />
              </div>
            ))}
          </div>

          {/* Orchestration Details Skeleton */}
          <div className="mt-6 space-y-4">
            <Skeleton className="h-6 w-48" />
            <div className="space-y-2">
              <Skeleton className="h-20 w-full rounded-lg" />
              <Skeleton className="h-20 w-full rounded-lg" />
              <Skeleton className="h-20 w-full rounded-lg" />
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

function ChatContent() {
  const [response, setResponse] = useState<CouncilResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showOrchestrationDetails, setShowOrchestrationDetails] = useState(true);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const responsePanelRef = useRef<HTMLDivElement>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [progressState, setProgressState] = useState<ProgressState>({
    stage: 'analysis',
    progress: 0,
    completedSubtasks: 0,
    totalSubtasks: 0,
    activeModels: [],
  });

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: 'k',
      ctrl: true,
      description: 'Focus chat input',
      callback: () => inputRef.current?.focus(),
    },
    {
      key: 'b',
      ctrl: true,
      description: 'Toggle chat history sidebar',
      callback: () => setSidebarOpen((prev) => !prev),
    },
    {
      key: '/',
      ctrl: true,
      description: 'Toggle orchestration details',
      callback: () => setShowOrchestrationDetails((prev) => !prev),
    },
    {
      key: 'Escape',
      description: 'Close response panel',
      callback: () => setResponse(null),
    },
    {
      key: 'n',
      ctrl: true,
      description: 'New chat',
      callback: () => {
        setResponse(null);
        setIsProcessing(false);
        setHasSubmitted(false);
      },
    },
    {
      key: '?',
      ctrl: true,
      description: 'Show keyboard shortcuts',
      callback: () => setShowShortcuts(true),
    },
  ]);

  const handleNewChat = () => {
    setResponse(null);
    setIsProcessing(false);
    setHasSubmitted(false);
  };

  const handleSubmit = async (content: string, mode: string) => {
    setIsProcessing(true);
    setResponse(null);
    setHasSubmitted(true);
    setProgressState({
      stage: 'analysis',
      progress: 0,
      completedSubtasks: 0,
      totalSubtasks: 0,
      activeModels: [],
    });
    // Processing will be handled by EnhancedChatInput component
  };

  const handleResponseReceived = (newResponse: CouncilResponse) => {
    setResponse(newResponse);
    setIsProcessing(false);
    setProgressState({
      stage: 'complete',
      progress: 100,
      completedSubtasks: 0,
      totalSubtasks: 0,
      activeModels: [],
    });
    
    // Smooth scroll to show response when ready
    setTimeout(() => {
      responsePanelRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
      });
    }, 100);
  };

  const handleProgressUpdate = (update: Partial<ProgressState>) => {
    setProgressState((prev) => ({ ...prev, ...update }));
  };

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Chat History Sidebar */}
      <ChatHistorySidebar
        open={sidebarOpen}
        onOpenChange={setSidebarOpen}
        onSelectConversation={handleNewChat}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane - Chat Input & Analytics */}
        <div
          className={`flex flex-col transition-all duration-300 ease-in-out ${
            response || isProcessing ? 'w-full md:w-[40%]' : 'w-full'
          } border-r border-border overflow-y-auto`}
        >
          <div 
            className={`flex-1 flex flex-col p-4 md:p-8 w-full transition-all duration-300 ease-in-out ${
              hasSubmitted ? 'justify-start max-w-full' : 'justify-center max-w-3xl mx-auto'
            }`}
          >
            {/* Chat Input - moves to top-left when submitted */}
            <div 
              className={`transition-all duration-300 ease-in-out ${
                hasSubmitted ? 'mb-4' : 'mb-8'
              }`}
            >
              <EnhancedChatInput
                onSubmit={handleSubmit}
                onResponseReceived={handleResponseReceived}
                onProgressUpdate={handleProgressUpdate}
                disabled={isProcessing}
              />
            </div>

            {/* Progress Indicator */}
            {isProcessing && (
              <div className="mb-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <ProgressIndicator
                  stage={progressState.stage}
                  progress={progressState.progress}
                  completedSubtasks={progressState.completedSubtasks}
                  totalSubtasks={progressState.totalSubtasks}
                  activeModels={progressState.activeModels}
                />
              </div>
            )}

            {/* Analytics Preview - moves below chat input when submitted */}
            <div 
              className={`transition-all duration-300 ease-in-out ${
                hasSubmitted ? 'opacity-100' : 'opacity-100'
              }`}
            >
              <AnalyticsPreview />
            </div>
          </div>
        </div>

        {/* Right Pane - Response with slide-in animation */}
        {(response || isProcessing) && (
          <div 
            ref={responsePanelRef}
            className={`hidden md:block w-[60%] overflow-hidden transition-all duration-300 ease-in-out ${
              response ? 'translate-x-0 opacity-100' : 'translate-x-4 opacity-90'
            }`}
          >
            {response ? (
              <ResponsePanel
                response={response}
                onClose={() => {
                  setResponse(null);
                  setHasSubmitted(false);
                }}
              />
            ) : (
              <ResponsePanelSkeleton />
            )}
          </div>
        )}

        {/* Mobile Response (Full Screen) */}
        {response && (
          <div className="md:hidden fixed inset-0 z-50 bg-background animate-in slide-in-from-bottom duration-300">
            <ResponsePanel
              response={response}
              onClose={() => {
                setResponse(null);
                setHasSubmitted(false);
              }}
            />
          </div>
        )}
      </div>

      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog open={showShortcuts} onOpenChange={setShowShortcuts} />
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <AuthenticatedLayout>
        <ChatContent />
      </AuthenticatedLayout>
    </ProtectedRoute>
  );
}
