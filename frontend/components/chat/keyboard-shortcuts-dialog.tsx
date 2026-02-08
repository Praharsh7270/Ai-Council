'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Keyboard } from 'lucide-react';

interface KeyboardShortcutsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const shortcuts = [
  {
    category: 'General',
    items: [
      { keys: ['Ctrl', 'Enter'], description: 'Send message' },
      { keys: ['Ctrl', 'K'], description: 'Focus chat input' },
      { keys: ['Ctrl', 'N'], description: 'New chat' },
      { keys: ['Ctrl', '?'], description: 'Show this help' },
    ],
  },
  {
    category: 'Navigation',
    items: [
      { keys: ['Ctrl', 'B'], description: 'Toggle chat history sidebar' },
      { keys: ['Ctrl', '/'], description: 'Toggle orchestration details' },
      { keys: ['Esc'], description: 'Close response panel' },
    ],
  },
];

export function KeyboardShortcutsDialog({ open, onOpenChange }: KeyboardShortcutsDialogProps) {
  const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  
  const formatKey = (key: string) => {
    if (key === 'Ctrl' && isMac) return 'Cmd';
    return key;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Use these keyboard shortcuts to navigate faster
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {shortcuts.map((category) => (
            <div key={category.category}>
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                {category.category}
              </h3>
              <div className="space-y-2">
                {category.items.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-accent transition-colors"
                  >
                    <span className="text-sm">{item.description}</span>
                    <div className="flex items-center gap-1">
                      {item.keys.map((key, keyIndex) => (
                        <span key={keyIndex} className="flex items-center gap-1">
                          <Badge variant="outline" className="font-mono text-xs px-2 py-1">
                            {formatKey(key)}
                          </Badge>
                          {keyIndex < item.keys.length - 1 && (
                            <span className="text-muted-foreground text-xs">+</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-muted rounded-lg text-sm text-muted-foreground">
          <strong>Tip:</strong> Press <Badge variant="outline" className="mx-1 font-mono text-xs">
            {isMac ? 'Cmd' : 'Ctrl'}
          </Badge> + <Badge variant="outline" className="mx-1 font-mono text-xs">?</Badge> anytime to see this help.
        </div>
      </DialogContent>
    </Dialog>
  );
}
