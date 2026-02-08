'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth-store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MessageSquare,
  History,
  Settings,
  User,
  Shield,
  LogOut,
  Menu,
  X,
  BarChart3,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface SidebarProps {
  className?: string;
}

interface ApiKeyStatus {
  configuredProviders: number;
  totalProviders: number;
  hasAnyKeys: boolean;
}

export function Sidebar({ className = '' }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [apiKeyStatus, setApiKeyStatus] = useState<ApiKeyStatus>({
    configuredProviders: 0,
    totalProviders: 0,
    hasAnyKeys: false,
  });

  useEffect(() => {
    fetchApiKeyStatus();
  }, [pathname]); // Refetch when route changes

  const fetchApiKeyStatus = async () => {
    try {
      const response = await apiClient.get('/api/v1/user/api-keys');
      const keys = response.data || [];
      const configuredCount = keys.filter((key: any) => key.is_active).length;
      
      setApiKeyStatus({
        configuredProviders: configuredCount,
        totalProviders: 6, // Total available providers
        hasAnyKeys: configuredCount > 0,
      });
    } catch (error) {
      // Silently fail - user might not have access to this endpoint yet
      console.debug('Could not fetch API key status:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  const navItems = [
    {
      label: 'Chat',
      icon: MessageSquare,
      href: '/chat',
      show: true,
    },
    {
      label: 'History',
      icon: History,
      href: '/history',
      show: true,
    },
    {
      label: 'Analytics',
      icon: BarChart3,
      href: '/dashboard',
      show: true,
    },
    {
      label: 'Settings',
      icon: Settings,
      href: '/settings',
      show: true,
      badge: !apiKeyStatus.hasAnyKeys ? 'Setup' : apiKeyStatus.configuredProviders > 0 ? apiKeyStatus.configuredProviders.toString() : undefined,
      badgeVariant: !apiKeyStatus.hasAnyKeys ? 'destructive' : 'default',
      highlight: !apiKeyStatus.hasAnyKeys,
    },
    {
      label: 'Admin',
      icon: Shield,
      href: '/admin',
      show: user?.role === 'admin',
    },
  ];

  const isActive = (href: string) => pathname === href;

  const SidebarContent = () => (
    <>
      {/* User Info */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          if (!item.show) return null;
          
          const Icon = item.icon;
          const active = isActive(item.href);
          
          return (
            <Button
              key={item.href}
              variant={active ? 'secondary' : 'ghost'}
              className={`w-full justify-start gap-3 ${
                item.highlight && !active ? 'border-2 border-orange-500 hover:border-orange-600' : ''
              }`}
              onClick={() => {
                router.push(item.href);
                setIsMobileOpen(false);
              }}
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <Badge 
                  variant={item.badgeVariant as any || 'default'}
                  className="ml-auto"
                >
                  {item.badge}
                </Badge>
              )}
            </Button>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-background border-r z-40 transform transition-transform duration-200 md:hidden ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        } ${className}`}
      >
        <div className="flex flex-col h-full pt-16">
          <SidebarContent />
        </div>
      </aside>

      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:flex md:flex-col w-64 bg-background border-r h-screen sticky top-0 ${className}`}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
