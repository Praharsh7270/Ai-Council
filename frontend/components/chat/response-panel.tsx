'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CouncilResponse } from '@/types/council';
import {
  X,
  Copy,
  Download,
  Share2,
  ChevronUp,
  Check,
  FileText,
  FileCode,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from '@/hooks/use-theme';
import { OrchestrationDetailPanel } from './orchestration-detail-panel';
import { ProgressIndicator } from './progress-indicator';

interface ResponsePanelProps {
  response: CouncilResponse;
  onClose: () => void;
}

export function ResponsePanel({ response, onClose }: ResponsePanelProps) {
  const [copied, setCopied] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const { theme } = useTheme();

  useEffect(() => {
    const handleScroll = () => {
      if (scrollRef.current) {
        setShowScrollTop(scrollRef.current.scrollTop > 300);
      }
    };

    const scrollElement = scrollRef.current;
    if (scrollElement) {
      scrollElement.addEventListener('scroll', handleScroll);
      return () => scrollElement.removeEventListener('scroll', handleScroll);
    }
  }, []);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(response.content);
      setCopied(true);
      toast({
        title: 'Copied!',
        description: 'Response copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  const handleDownload = (format: 'txt' | 'md' | 'json') => {
    let content: string;
    let filename: string;
    let mimeType: string;

    switch (format) {
      case 'json':
        content = JSON.stringify(response, null, 2);
        filename = `response-${response.requestId}.json`;
        mimeType = 'application/json';
        break;
      case 'md':
        content = `# AI Council Response\n\n${response.content}\n\n---\n\n**Confidence:** ${response.confidence}\n**Execution Time:** ${response.executionTime}s\n**Total Cost:** $${response.totalCost.toFixed(4)}`;
        filename = `response-${response.requestId}.md`;
        mimeType = 'text/markdown';
        break;
      default:
        content = response.content;
        filename = `response-${response.requestId}.txt`;
        mimeType = 'text/plain';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: 'Downloaded!',
      description: `Response saved as ${filename}`,
    });
  };

  const handleShare = async () => {
    // TODO: Implement sharing functionality
    toast({
      title: 'Coming Soon',
      description: 'Sharing functionality will be available soon',
    });
  };

  const scrollToTop = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const renderContent = () => {
    const content = response.content;
    
    // Check if content contains code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts: JSX.Element[] = [];
    let lastIndex = 0;
    let match;
    let key = 0;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textContent = content.substring(lastIndex, match.index);
        parts.push(
          <div key={`text-${key++}`} className="whitespace-pre-wrap mb-4">
            {textContent}
          </div>
        );
      }

      // Add code block with syntax highlighting
      const language = match[1] || 'text';
      const code = match[2];
      parts.push(
        <div key={`code-${key++}`} className="mb-4 rounded-lg overflow-hidden">
          <div className="bg-muted px-4 py-2 text-xs font-mono flex items-center justify-between">
            <span>{language}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(code);
                toast({ title: 'Code copied!' });
              }}
            >
              <Copy className="h-3 w-3" />
            </Button>
          </div>
          <SyntaxHighlighter
            language={language}
            style={theme === 'dark' ? vscDarkPlus : vs}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: '0.875rem',
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <div key={`text-${key++}`} className="whitespace-pre-wrap">
          {content.substring(lastIndex)}
        </div>
      );
    }

    return parts.length > 0 ? parts : <div className="whitespace-pre-wrap">{content}</div>;
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">Response</h2>
        <div className="flex items-center gap-2">
          {/* Action Buttons */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleCopy}
            title="Copy to clipboard"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          </Button>

          <div className="relative group">
            <Button
              variant="ghost"
              size="icon"
              title="Download"
            >
              <Download className="h-4 w-4" />
            </Button>
            <div className="absolute right-0 top-full mt-1 hidden group-hover:block bg-popover border rounded-md shadow-lg z-10">
              <div className="p-1 space-y-1 min-w-[120px]">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => handleDownload('txt')}
                >
                  <FileText className="h-3 w-3 mr-2" />
                  Text (.txt)
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => handleDownload('md')}
                >
                  <FileCode className="h-3 w-3 mr-2" />
                  Markdown (.md)
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => handleDownload('json')}
                >
                  <FileCode className="h-3 w-3 mr-2" />
                  JSON (.json)
                </Button>
              </div>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleShare}
            title="Share"
          >
            <Share2 className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            title="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="p-6 space-y-4">
          {/* Response Content */}
          <div className="prose dark:prose-invert max-w-none">
            {renderContent()}
          </div>

          {/* Metadata */}
          <div className="mt-8 pt-6 border-t grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Confidence</div>
              <div className="text-lg font-semibold">
                {(response.confidence * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Execution Time</div>
              <div className="text-lg font-semibold">{response.executionTime.toFixed(2)}s</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Total Cost</div>
              <div className="text-lg font-semibold">${response.totalCost.toFixed(4)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Models Used</div>
              <div className="text-lg font-semibold">{response.modelsUsed?.length || 0}</div>
            </div>
          </div>

          {/* Orchestration Details */}
          <OrchestrationDetailPanel response={response} />
        </div>
      </ScrollArea>

      {/* Scroll to Top Button */}
      {showScrollTop && (
        <Button
          variant="secondary"
          size="icon"
          className="fixed bottom-6 right-6 rounded-full shadow-lg"
          onClick={scrollToTop}
        >
          <ChevronUp className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
