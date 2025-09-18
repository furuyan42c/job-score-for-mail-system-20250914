'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import { SqlEditorProps, SqlQuery, SqlQueryResult, SqlTemplate } from '@/types';
import { clsx } from 'clsx';
import { Play, History, FileText, Download, Loader2, AlertCircle } from 'lucide-react';
import QueryHistory from './QueryHistory';
import ResultsTable from './ResultsTable';

// Dynamically import Monaco editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-6 h-6 animate-spin" />
    </div>
  ),
  ssr: false,
});

const DEFAULT_TEMPLATES: SqlTemplate[] = [
  {
    id: '1',
    name: 'Recent Jobs',
    description: 'Get jobs posted in the last 7 days',
    category: 'jobs',
    query: `SELECT
  id,
  title,
  company,
  location,
  salary_min,
  salary_max,
  posted_at
FROM jobs
WHERE posted_at >= NOW() - INTERVAL '7 days'
ORDER BY posted_at DESC
LIMIT 20;`,
  },
  {
    id: '2',
    name: 'User Registrations',
    description: 'Count of user registrations by day',
    category: 'users',
    query: `SELECT
  DATE(created_at) as registration_date,
  COUNT(*) as user_count
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY registration_date DESC;`,
  },
  {
    id: '3',
    name: 'Top Matches',
    description: 'Highest scoring job matches',
    category: 'matches',
    query: `SELECT
  jm.id,
  u.email as user_email,
  j.title as job_title,
  j.company,
  jm.score,
  jm.created_at
FROM job_matches jm
JOIN users u ON jm.user_id = u.id
JOIN jobs j ON jm.job_id = j.id
WHERE jm.score >= 0.8
ORDER BY jm.score DESC, jm.created_at DESC
LIMIT 15;`,
  },
];

export default function SqlEditor({
  initialQuery = '',
  onQueryExecute,
  readOnly = false,
  height = '400px',
  showHistory = true,
  autoComplete = true,
  templates = DEFAULT_TEMPLATES,
  className,
  'data-testid': testId,
}: SqlEditorProps) {
  const [query, setQuery] = useState(initialQuery);
  const [result, setResult] = useState<SqlQueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryHistory, setQueryHistory] = useState<SqlQuery[]>([]);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const editorRef = useRef<any>(null);

  // Load query history from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('sql-query-history');
      if (saved) {
        const parsed = JSON.parse(saved);
        setQueryHistory(parsed.map((q: any) => ({
          ...q,
          timestamp: new Date(q.timestamp),
        })));
      }
    } catch (err) {
      console.warn('Failed to load query history:', err);
    }
  }, []);

  // Save query history to localStorage
  const saveQueryHistory = useCallback((queries: SqlQuery[]) => {
    try {
      localStorage.setItem('sql-query-history', JSON.stringify(queries));
    } catch (err) {
      console.warn('Failed to save query history:', err);
    }
  }, []);

  const addToHistory = useCallback((query: string, result?: SqlQueryResult, error?: string) => {
    const historyItem: SqlQuery = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      query: query.trim(),
      timestamp: new Date(),
      executionTime: result?.executionTime,
      rowCount: result?.rowCount,
      error,
    };

    setQueryHistory(prev => {
      const newHistory = [historyItem, ...prev.slice(0, 99)]; // Keep last 100 queries
      saveQueryHistory(newHistory);
      return newHistory;
    });
  }, [saveQueryHistory]);

  const executeQuery = useCallback(async () => {
    if (!query.trim() || !onQueryExecute) return;

    // Basic validation - only allow SELECT queries for security
    const trimmedQuery = query.trim().toLowerCase();
    if (!trimmedQuery.startsWith('select')) {
      setError('Only SELECT queries are allowed for security reasons.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const startTime = Date.now();
      const queryResult = await onQueryExecute(query);
      const executionTime = Date.now() - startTime;

      const finalResult = { ...queryResult, executionTime };
      setResult(finalResult);
      addToHistory(query, finalResult);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query execution failed';
      setError(errorMessage);
      addToHistory(query, undefined, errorMessage);
    } finally {
      setLoading(false);
    }
  }, [query, onQueryExecute, addToHistory]);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;

    // Configure editor for SQL
    if (autoComplete) {
      // Register SQL completion provider
      editor.getModel()?.updateOptions({
        tabSize: 2,
        insertSpaces: true
      });
    }
  };

  const handleQuerySelect = (selectedQuery: SqlQuery) => {
    setQuery(selectedQuery.query);
    setShowHistoryPanel(false);
    editorRef.current?.focus();
  };

  const handleTemplateSelect = (template: SqlTemplate) => {
    setQuery(template.query);
    setShowTemplates(false);
    editorRef.current?.focus();
  };

  const handleQueryDelete = (queryId: string) => {
    setQueryHistory(prev => {
      const newHistory = prev.filter(q => q.id !== queryId);
      saveQueryHistory(newHistory);
      return newHistory;
    });
  };

  const exportToCsv = useCallback(() => {
    if (!result) return;

    const csvContent = [
      // Header row
      result.columns.map(col => col.name).join(','),
      // Data rows
      ...result.rows.map(row =>
        result.columns.map(col => {
          const value = row[col.name];
          // Escape commas and quotes in CSV
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? '';
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-results-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [result]);

  return (
    <div className={clsx('bg-white rounded-lg border shadow-sm', className)} data-testid={testId}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
        <h3 className="text-lg font-semibold text-gray-900">SQL Query Editor</h3>
        <div className="flex items-center space-x-2">
          {showHistory && (
            <button
              onClick={() => setShowHistoryPanel(!showHistoryPanel)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-md transition-colors"
              title="Query History"
            >
              <History className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-md transition-colors"
            title="Query Templates"
          >
            <FileText className="w-4 h-4" />
          </button>
          {result && (
            <button
              onClick={exportToCsv}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-md transition-colors"
              title="Export to CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={executeQuery}
            disabled={loading || !query.trim() || readOnly}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            <span>{loading ? 'Running...' : 'Run Query'}</span>
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Main editor area */}
        <div className="flex-1">
          {/* Template selector */}
          {showTemplates && (
            <div className="p-4 border-b bg-gray-50">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Query Templates</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className="text-left p-3 border rounded-md hover:bg-white hover:shadow-sm transition-colors"
                  >
                    <div className="font-medium text-sm text-gray-900">{template.name}</div>
                    <div className="text-xs text-gray-600 mt-1">{template.description}</div>
                    <div className="text-xs text-blue-600 mt-1 capitalize">{template.category}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Editor */}
          <div className="relative">
            <MonacoEditor
              height={height}
              language="sql"
              value={query}
              onChange={(value) => setQuery(value || '')}
              onMount={handleEditorDidMount}
              options={{
                readOnly,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                automaticLayout: true,
                theme: 'vs',
                suggestOnTriggerCharacters: autoComplete,
                quickSuggestions: autoComplete,
                wordBasedSuggestions: 'off',
              }}
              className="border-0"
            />
          </div>

          {/* Error display */}
          {error && (
            <div className="p-4 border-t bg-red-50 border-red-200">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium text-red-800">Query Error</div>
                  <div className="text-sm text-red-700 mt-1">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          <ResultsTable
            result={result}
            loading={loading}
            error={error}
            onExportCsv={exportToCsv}
            className="border-t"
          />
        </div>

        {/* History sidebar */}
        {showHistory && showHistoryPanel && (
          <QueryHistory
            queries={queryHistory}
            onQuerySelect={handleQuerySelect}
            onQueryDelete={handleQueryDelete}
            className="w-80 border-l"
          />
        )}
      </div>
    </div>
  );
}