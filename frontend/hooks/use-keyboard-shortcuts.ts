'use client';

import { useEffect, useCallback } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  cmd?: boolean;
  shift?: boolean;
  alt?: boolean;
  callback: () => void;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[], enabled: boolean = true) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      for (const shortcut of shortcuts) {
        const ctrlOrCmd = shortcut.ctrl || shortcut.cmd;
        const isCtrlOrCmdPressed = event.ctrlKey || event.metaKey;
        
        const matches =
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          (!ctrlOrCmd || isCtrlOrCmdPressed) &&
          (!shortcut.shift || event.shiftKey) &&
          (!shortcut.alt || event.altKey);

        if (matches) {
          event.preventDefault();
          shortcut.callback();
          break;
        }
      }
    },
    [shortcuts, enabled]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

export const CHAT_SHORTCUTS: KeyboardShortcut[] = [
  {
    key: 'Enter',
    ctrl: true,
    description: 'Send message',
    callback: () => {}, // Will be overridden
  },
  {
    key: 'k',
    ctrl: true,
    description: 'Focus chat input',
    callback: () => {}, // Will be overridden
  },
  {
    key: 'b',
    ctrl: true,
    description: 'Toggle chat history sidebar',
    callback: () => {}, // Will be overridden
  },
  {
    key: '/',
    ctrl: true,
    description: 'Toggle orchestration details',
    callback: () => {}, // Will be overridden
  },
  {
    key: 'Escape',
    description: 'Close response panel',
    callback: () => {}, // Will be overridden
  },
  {
    key: 'n',
    ctrl: true,
    description: 'New chat',
    callback: () => {}, // Will be overridden
  },
  {
    key: '?',
    ctrl: true,
    description: 'Show keyboard shortcuts',
    callback: () => {}, // Will be overridden
  },
];
