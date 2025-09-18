'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Database,
  Play,
  Download,
  Clock,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Copy,
  History,
  Trash2,
  Settings,
  RefreshCw,
  Terminal,
  FileText,
  ChevronDown,
  ChevronRight,
  Loader2,
  StopCircle,
  Activity,
  TrendingUp,
  Users,
  Server,
  MonitorIcon,
  ZapIcon,
} from 'lucide-react';

// Types for SQL execution
interface QueryResult {
  columns: string[];
  rows: any[][];
  rowCount: number;
  executionTime: number;
  timestamp: string;
}

interface QueryHistory {
  id: string;
  query: string;
  timestamp: string;
  executionTime: number;
  status: 'success' | 'error';
  rowCount?: number;
  error?: string;
}

interface DatabaseMetrics {
  activeConnections: number;
  totalQueries: number;
  avgQueryTime: number;
  slowQueries: number;
  errorRate: number;
  uptime: string;
}

interface QueryExecutionMetrics {
  totalExecuted: number;
  successfulQueries: number;
  failedQueries: number;
  avgExecutionTime: number;
  totalRowsReturned: number;
  lastExecutionTime: string;
}

// Mock data generators
const generateMockDatabaseMetrics = (): DatabaseMetrics => ({
  activeConnections: Math.floor(Math.random() * 20) + 5,
  totalQueries: Math.floor(Math.random() * 10000) + 50000,
  avgQueryTime: Math.floor(Math.random() * 50) + 25,
  slowQueries: Math.floor(Math.random() * 10) + 2,
  errorRate: Math.random() * 2,
  uptime: `${Math.floor(Math.random() * 30) + 1} days`,
});

const generateMockExecutionMetrics = (): QueryExecutionMetrics => ({
  totalExecuted: Math.floor(Math.random() * 1000) + 500,
  successfulQueries: Math.floor(Math.random() * 900) + 400,
  failedQueries: Math.floor(Math.random() * 50) + 10,
  avgExecutionTime: Math.floor(Math.random() * 200) + 50,
  totalRowsReturned: Math.floor(Math.random() * 100000) + 10000,
  lastExecutionTime: new Date().toISOString(),
});

// Sample queries for quick access
const SAMPLE_QUERIES = [
  {
    name: 'Active Jobs Count',
    query: 'SELECT COUNT(*) as active_jobs FROM jobs WHERE status = \'active\';'
  },
  {
    name: 'User Registration Stats',
    query: 'SELECT DATE(created_at) as date, COUNT(*) as registrations\nFROM users \nWHERE created_at >= CURRENT_DATE - INTERVAL 30 DAY\nGROUP BY DATE(created_at)\nORDER BY date DESC;'
  },
  {
    name: 'Job Matching Success Rate',
    query: 'SELECT \n  job_category,\n  COUNT(*) as total_applications,\n  SUM(CASE WHEN status = \'matched\' THEN 1 ELSE 0 END) as matches,\n  ROUND((SUM(CASE WHEN status = \'matched\' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as success_rate\nFROM job_applications ja\nJOIN jobs j ON ja.job_id = j.id\nGROUP BY job_category\nORDER BY success_rate DESC;'
  },
  {
    name: 'Recent Email Campaigns',
    query: 'SELECT \n  campaign_name,\n  sent_count,\n  open_rate,\n  click_rate,\n  created_at\nFROM email_campaigns \nWHERE created_at >= CURRENT_DATE - INTERVAL 7 DAY\nORDER BY created_at DESC\nLIMIT 10;'
  },
  {
    name: 'Database Table Sizes',
    query: 'SELECT \n  table_name,\n  ROUND(((data_length + index_length) / 1024 / 1024), 2) AS \'Size (MB)\',\n  table_rows as \'Row Count\'\nFROM information_schema.tables \nWHERE table_schema = DATABASE()\nORDER BY (data_length + index_length) DESC;'
  }
];

export default function SQLMonitoringPage() {
  // SQL Editor State
  const [currentQuery, setCurrentQuery] = useState('-- Enter your SQL query here\nSELECT * FROM users LIMIT 10;');
  const [isExecuting, setIsExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // History and metrics
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [dbMetrics, setDbMetrics] = useState<DatabaseMetrics>(generateMockDatabaseMetrics());
  const [executionMetrics, setExecutionMetrics] = useState<QueryExecutionMetrics>(generateMockExecutionMetrics());

  // UI State
  const [selectedTab, setSelectedTab] = useState('sql-console');
  const [historyExpanded, setHistoryExpanded] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-refresh metrics
  useEffect(() => {
    const interval = setInterval(() => {
      setDbMetrics(generateMockDatabaseMetrics());
      setExecutionMetrics(generateMockExecutionMetrics());
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Mock SQL execution
  const executeQuery = useCallback(async () => {
    if (!currentQuery.trim() || isExecuting) return;

    setIsExecuting(true);
    setQueryError(null);
    setQueryResult(null);

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1200));

      // Simulate different types of results based on query
      const queryLower = currentQuery.toLowerCase();
      let mockResult: QueryResult;

      if (queryLower.includes('count(*)')) {
        mockResult = {
          columns: ['count'],
          rows: [[Math.floor(Math.random() * 10000) + 100]],
          rowCount: 1,
          executionTime: Math.floor(Math.random() * 100) + 10,
          timestamp: new Date().toISOString(),
        };
      } else if (queryLower.includes('users')) {
        const userCount = Math.floor(Math.random() * 20) + 5;
        mockResult = {
          columns: ['id', 'name', 'email', 'created_at', 'status'],
          rows: Array.from({ length: userCount }, (_, i) => [
            i + 1,
            `User ${i + 1}`,
            `user${i + 1}@example.com`,
            new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            Math.random() > 0.8 ? 'inactive' : 'active'
          ]),
          rowCount: userCount,
          executionTime: Math.floor(Math.random() * 150) + 20,
          timestamp: new Date().toISOString(),
        };
      } else if (queryLower.includes('jobs')) {
        const jobCount = Math.floor(Math.random() * 15) + 3;
        mockResult = {
          columns: ['id', 'title', 'company', 'location', 'salary', 'status'],
          rows: Array.from({ length: jobCount }, (_, i) => [
            i + 1,
            `Software Engineer ${i + 1}`,
            `Company ${String.fromCharCode(65 + i)}`,
            ['New York', 'San Francisco', 'London', 'Tokyo'][Math.floor(Math.random() * 4)],
            `$${(Math.floor(Math.random() * 100) + 50)}k`,
            ['active', 'inactive', 'filled'][Math.floor(Math.random() * 3)]
          ]),
          rowCount: jobCount,
          executionTime: Math.floor(Math.random() * 200) + 30,
          timestamp: new Date().toISOString(),
        };
      } else {
        // Generic result
        const rowCount = Math.floor(Math.random() * 50) + 1;
        mockResult = {
          columns: ['column1', 'column2', 'column3'],
          rows: Array.from({ length: rowCount }, (_, i) => [
            `Value ${i + 1}`,
            Math.floor(Math.random() * 1000),
            Math.random() > 0.5 ? 'Yes' : 'No'
          ]),
          rowCount: rowCount,
          executionTime: Math.floor(Math.random() * 300) + 50,
          timestamp: new Date().toISOString(),
        };
      }

      // Randomly simulate errors (5% chance)
      if (Math.random() < 0.05) {
        throw new Error('Syntax error: Unknown column \'invalid_column\' in \'field list\'');
      }

      setQueryResult(mockResult);

      // Add to history
      const historyEntry: QueryHistory = {
        id: Date.now().toString(),
        query: currentQuery,
        timestamp: new Date().toISOString(),
        executionTime: mockResult.executionTime,
        status: 'success',
        rowCount: mockResult.rowCount,
      };

      setQueryHistory(prev => [historyEntry, ...prev.slice(0, 49)]); // Keep last 50

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setQueryError(errorMessage);

      // Add error to history
      const historyEntry: QueryHistory = {
        id: Date.now().toString(),
        query: currentQuery,
        timestamp: new Date().toISOString(),
        executionTime: 0,
        status: 'error',
        error: errorMessage,
      };

      setQueryHistory(prev => [historyEntry, ...prev.slice(0, 49)]);
    } finally {
      setIsExecuting(false);
    }
  }, [currentQuery, isExecuting]);

  // Export results to CSV
  const exportToCSV = useCallback(() => {
    if (!queryResult) return;

    const csvContent = [
      queryResult.columns.join(','),
      ...queryResult.rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `query_result_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [queryResult]);

  // Load query from history
  const loadQueryFromHistory = useCallback((historyItem: QueryHistory) => {
    setCurrentQuery(historyItem.query);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Load sample query
  const loadSampleQuery = useCallback((query: string) => {
    setCurrentQuery(query);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Clear history
  const clearHistory = useCallback(() => {
    setQueryHistory([]);
  }, []);

  // Pagination for results
  const paginatedRows = queryResult?.rows.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  ) || [];

  const totalPages = queryResult ? Math.ceil(queryResult.rows.length / pageSize) : 0;

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SQL Monitoring Console</h1>
          <p className="text-muted-foreground">Execute SQL queries and monitor database performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="flex items-center space-x-1">
            <Database className="h-3 w-3" />
            <span>Connected</span>
          </Badge>
          <Badge variant="secondary" className="flex items-center space-x-1">
            <Activity className="h-3 w-3" />
            <span>{dbMetrics.activeConnections} connections</span>
          </Badge>
        </div>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="sql-console" className="flex items-center space-x-2">
            <Terminal className="h-4 w-4" />
            <span>SQL Console</span>
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Performance</span>
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center space-x-2">
            <MonitorIcon className="h-4 w-4" />
            <span>Database Stats</span>
          </TabsTrigger>
        </TabsList>

        {/* SQL Console Tab */}
        <TabsContent value="sql-console" className="space-y-6">
          <ResizablePanelGroup direction="horizontal" className="min-h-[600px] rounded-lg border">
            {/* Query History Sidebar */}
            <ResizablePanel defaultSize={25} minSize={20}>
              <div className="h-full flex flex-col">
                <div className="p-4 border-b">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <History className="h-4 w-4" />
                      <span className="font-medium">Query History</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setHistoryExpanded(!historyExpanded)}
                    >
                      {historyExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </Button>
                  </div>

                  {/* Sample Queries */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium mb-2">Sample Queries</h4>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="w-full justify-start">
                          <FileText className="h-4 w-4 mr-2" />
                          Load Sample
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" className="w-56">
                        {SAMPLE_QUERIES.map((sample, index) => (
                          <DropdownMenuItem
                            key={index}
                            onClick={() => loadSampleQuery(sample.query)}
                          >
                            {sample.name}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  {queryHistory.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={clearHistory}
                      className="w-full"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Clear History
                    </Button>
                  )}
                </div>

                {historyExpanded && (
                  <ScrollArea className="flex-1 p-4">
                    {queryHistory.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No queries executed yet
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {queryHistory.map((item) => (
                          <div
                            key={item.id}
                            className="p-3 border rounded-lg cursor-pointer hover:bg-accent transition-colors"
                            onClick={() => loadQueryFromHistory(item)}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <Badge
                                variant={item.status === 'success' ? 'default' : 'destructive'}
                                className="text-xs"
                              >
                                {item.status === 'success' ? (
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                ) : (
                                  <AlertCircle className="h-3 w-3 mr-1" />
                                )}
                                {item.status}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {item.executionTime}ms
                              </span>
                            </div>
                            <p className="text-xs font-mono bg-muted p-2 rounded truncate">
                              {item.query.split('\n')[0]}
                            </p>
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                              {item.rowCount !== undefined && (
                                <span>{item.rowCount} rows</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                )}
              </div>
            </ResizablePanel>

            <ResizableHandle />

            {/* Main SQL Editor and Results */}
            <ResizablePanel defaultSize={75}>
              <div className="h-full flex flex-col">
                {/* SQL Editor */}
                <div className="p-4 border-b">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium">SQL Query Editor</h3>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigator.clipboard.writeText(currentQuery)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        onClick={executeQuery}
                        disabled={isExecuting || !currentQuery.trim()}
                        className="flex items-center space-x-2"
                      >
                        {isExecuting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        <span>{isExecuting ? 'Executing...' : 'Execute'}</span>
                      </Button>
                    </div>
                  </div>

                  <Textarea
                    ref={textareaRef}
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    placeholder="Enter your SQL query here..."
                    className="min-h-[150px] font-mono text-sm"
                    onKeyDown={(e) => {
                      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                        e.preventDefault();
                        executeQuery();
                      }
                    }}
                  />

                  <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                    <span>Press Ctrl+Enter to execute</span>
                    {currentQuery && (
                      <span>{currentQuery.length} characters</span>
                    )}
                  </div>
                </div>

                {/* Query Results */}
                <div className="flex-1 p-4">
                  {queryError && (
                    <Card className="mb-4 border-destructive">
                      <CardHeader className="pb-3">
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="h-4 w-4 text-destructive" />
                          <CardTitle className="text-sm text-destructive">Query Error</CardTitle>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <pre className="text-sm bg-destructive/10 p-3 rounded font-mono whitespace-pre-wrap">
                          {queryError}
                        </pre>
                      </CardContent>
                    </Card>
                  )}

                  {queryResult && (
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="flex items-center space-x-2">
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span>Query Results</span>
                            </CardTitle>
                            <CardDescription>
                              {queryResult.rowCount} rows returned in {queryResult.executionTime}ms
                            </CardDescription>
                          </div>
                          <div className="flex items-center space-x-2">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="outline" size="sm">
                                  <Settings className="h-4 w-4 mr-2" />
                                  {pageSize} per page
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                {[25, 50, 100, 200].map((size) => (
                                  <DropdownMenuItem
                                    key={size}
                                    onClick={() => {
                                      setPageSize(size);
                                      setCurrentPage(1);
                                    }}
                                  >
                                    {size} rows
                                  </DropdownMenuItem>
                                ))}
                              </DropdownMenuContent>
                            </DropdownMenu>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={exportToCSV}
                            >
                              <Download className="h-4 w-4 mr-2" />
                              Export CSV
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="border rounded-lg overflow-hidden">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                {queryResult.columns.map((column, index) => (
                                  <TableHead key={index} className="font-medium">
                                    {column}
                                  </TableHead>
                                ))}
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {paginatedRows.map((row, rowIndex) => (
                                <TableRow key={rowIndex}>
                                  {row.map((cell, cellIndex) => (
                                    <TableCell key={cellIndex} className="font-mono text-sm">
                                      {cell === null ? (
                                        <span className="text-muted-foreground italic">NULL</span>
                                      ) : (
                                        String(cell)
                                      )}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>

                        {totalPages > 1 && (
                          <div className="flex items-center justify-between mt-4">
                            <p className="text-sm text-muted-foreground">
                              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, queryResult.rowCount)} of {queryResult.rowCount} results
                            </p>
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1}
                              >
                                Previous
                              </Button>
                              <span className="text-sm">
                                Page {currentPage} of {totalPages}
                              </span>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages}
                              >
                                Next
                              </Button>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {!queryResult && !queryError && !isExecuting && (
                    <Card className="border-dashed">
                      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                        <Database className="h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium mb-2">Ready to Execute</h3>
                        <p className="text-muted-foreground">
                          Write your SQL query above and click Execute to see results here.
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Queries Executed</CardTitle>
                <ZapIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{executionMetrics.totalExecuted}</div>
                <p className="text-xs text-muted-foreground">
                  {executionMetrics.successfulQueries} successful
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Execution Time</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{executionMetrics.avgExecutionTime}ms</div>
                <p className="text-xs text-muted-foreground">
                  Last: {new Date(executionMetrics.lastExecutionTime).toLocaleTimeString()}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Rows Returned</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{executionMetrics.totalRowsReturned.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  Total rows returned
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((executionMetrics.successfulQueries / executionMetrics.totalExecuted) * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {executionMetrics.failedQueries} failed queries
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Query Performance</CardTitle>
              <CardDescription>Query execution times and success rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {queryHistory.slice(0, 10).map((query, index) => (
                  <div key={query.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono truncate">{query.query.split('\n')[0]}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(query.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4 ml-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{query.executionTime}ms</p>
                        {query.rowCount !== undefined && (
                          <p className="text-xs text-muted-foreground">{query.rowCount} rows</p>
                        )}
                      </div>
                      <Badge variant={query.status === 'success' ? 'default' : 'destructive'}>
                        {query.status === 'success' ? (
                          <CheckCircle className="h-3 w-3 mr-1" />
                        ) : (
                          <AlertCircle className="h-3 w-3 mr-1" />
                        )}
                        {query.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Database Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.activeConnections}</div>
                <p className="text-xs text-muted-foreground">
                  Database connections
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.totalQueries.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  Since last restart
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Query Time</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.avgQueryTime}ms</div>
                <p className="text-xs text-muted-foreground">
                  Database average
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Slow Queries</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.slowQueries}</div>
                <p className="text-xs text-muted-foreground">
                  Queries &gt; 1000ms
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.errorRate.toFixed(2)}%</div>
                <p className="text-xs text-muted-foreground">
                  Query error rate
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Database Uptime</CardTitle>
                <Server className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dbMetrics.uptime}</div>
                <p className="text-xs text-muted-foreground">
                  System uptime
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Database Health Status</CardTitle>
              <CardDescription>Real-time database health monitoring</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">Database Connection</p>
                      <p className="text-sm text-muted-foreground">Primary database is responding normally</p>
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-800">Healthy</Badge>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">Query Performance</p>
                      <p className="text-sm text-muted-foreground">Average response time within normal range</p>
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-800">Good</Badge>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    <div>
                      <p className="font-medium">Connection Pool</p>
                      <p className="text-sm text-muted-foreground">High connection usage detected</p>
                    </div>
                  </div>
                  <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">Disk Space</p>
                      <p className="text-sm text-muted-foreground">Sufficient storage available</p>
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-800">Normal</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}