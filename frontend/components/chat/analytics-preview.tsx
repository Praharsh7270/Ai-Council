'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';
import { ChevronDown, ChevronUp, TrendingUp, DollarSign, Target, BarChart3 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface UserStats {
  totalRequests: number;
  totalCost: number;
  averageConfidence: number;
  requestsByMode: Record<string, number>;
  requestsOverTime: Array<{ date: string; count: number }>;
  topModels: Array<{ model: string; count: number }>;
}

export function AnalyticsPreview() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/v1/user/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!stats && !isLoading) {
    return null;
  }

  const last7Days = stats?.requestsOverTime?.slice(-7) || [];
  const maxCount = Math.max(...last7Days.map((d) => d.count), 1);

  return (
    <Card className="border-dashed">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Quick Stats
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Compact Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <TrendingUp className="h-3 w-3" />
              <span className="text-xs">Queries</span>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : stats?.totalRequests || 0}
            </div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <DollarSign className="h-3 w-3" />
              <span className="text-xs">Cost</span>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : `$${(stats?.totalCost || 0).toFixed(2)}`}
            </div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <Target className="h-3 w-3" />
              <span className="text-xs">Avg Score</span>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : `${((stats?.averageConfidence || 0) * 100).toFixed(0)}%`}
            </div>
          </div>
        </div>

        {/* Expanded View */}
        {isExpanded && stats && (
          <>
            {/* Mini Chart - Last 7 Days */}
            <div className="pt-4 border-t">
              <div className="text-xs text-muted-foreground mb-2">Last 7 Days</div>
              <div className="flex items-end justify-between gap-1 h-16">
                {last7Days.map((day, index) => {
                  const height = (day.count / maxCount) * 100;
                  return (
                    <div
                      key={index}
                      className="flex-1 flex flex-col items-center gap-1"
                    >
                      <div
                        className="w-full bg-primary rounded-t transition-all hover:opacity-80"
                        style={{ height: `${height}%`, minHeight: day.count > 0 ? '4px' : '0' }}
                        title={`${day.count} queries`}
                      />
                      <div className="text-[10px] text-muted-foreground">
                        {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })[0]}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Provider Usage */}
            {stats.topModels && stats.topModels.length > 0 && (
              <div className="pt-4 border-t">
                <div className="text-xs text-muted-foreground mb-2">Top Providers</div>
                <div className="space-y-2">
                  {stats.topModels.slice(0, 3).map((model, index) => {
                    const percentage = (model.count / stats.totalRequests) * 100;
                    return (
                      <div key={index} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="truncate">{model.model}</span>
                          <span className="text-muted-foreground">{model.count}</span>
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
            )}

            {/* View Full Analytics Link */}
            <div className="pt-4 border-t">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => router.push('/dashboard')}
              >
                View Full Analytics
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
