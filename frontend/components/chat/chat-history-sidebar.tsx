'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { councilApi } from '@/lib/council-api';
import { MessageSquare, Search, Trash2, Plus, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { formatDistanceToNow } from 'date-fns';

interface Conversation {
  id: string;
  content: string;
  createdAt: string;
  executionMode: string;
  status: string;
}

interface ChatHistorySidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectConversation: (conversation: Conversation) => void;
}

export function ChatHistorySidebar({
  open,
  onOpenChange,
  onSelectConversation,
}: ChatHistorySidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [filteredConversations, setFilteredConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (open) {
      loadConversations();
    }
  }, [open]);

  useEffect(() => {
    // Filter conversations based on search query
    if (searchQuery.trim()) {
      const filtered = conversations.filter((conv) =>
        conv.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredConversations(filtered);
    } else {
      setFilteredConversations(conversations);
    }
  }, [searchQuery, conversations]);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const response = await councilApi.getHistory({
        page: 1,
        limit: 50,
      });
      setConversations(response.items);
      setFilteredConversations(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load conversation history',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await councilApi.deleteRequest(id);
      setConversations((prev) => prev.filter((conv) => conv.id !== id));
      toast({
        title: 'Success',
        description: 'Conversation deleted',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete conversation',
        variant: 'destructive',
      });
    } finally {
      setDeleteId(null);
    }
  };

  const handleNewChat = () => {
    onSelectConversation({
      id: '',
      content: '',
      createdAt: new Date().toISOString(),
      executionMode: 'balanced',
      status: 'new',
    });
    onOpenChange(false);
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="left" className="w-80 p-0">
          <SheetHeader className="p-4 border-b">
            <SheetTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Chat History
            </SheetTitle>
          </SheetHeader>

          {/* New Chat Button */}
          <div className="p-4 border-b">
            <Button
              onClick={handleNewChat}
              className="w-full"
              variant="default"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Search */}
          <div className="p-4 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Conversations List */}
          <ScrollArea className="flex-1 h-[calc(100vh-220px)]">
            {isLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                {searchQuery ? 'No conversations found' : 'No conversations yet'}
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {filteredConversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className="group relative p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => {
                      onSelectConversation(conversation);
                      onOpenChange(false);
                    }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {truncateText(conversation.content)}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(conversation.createdAt), {
                              addSuffix: true,
                            })}
                          </span>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                            {conversation.executionMode}
                          </span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteId(conversation.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Conversation</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this conversation? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteId && handleDelete(deleteId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
