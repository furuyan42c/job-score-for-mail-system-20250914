'use client';

import React from 'react';
import { QueryHistoryProps, SqlQuery } from '@/types';
import { clsx } from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import { Clock, Trash2, CheckCircle, XCircle, Timer } from 'lucide-react';

export default function QueryHistory({
  queries,
  onQuerySelect,
  onQueryDelete,
  maxItems = 50,
  className,
  'data-testid': testId,
}: QueryHistoryProps) {
  const displayQueries = queries.slice(0, maxItems);

  const formatExecutionTime = (ms?: number) => {
    if (ms === undefined) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusIcon = (query: SqlQuery) => {
    if (query.error) {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
    if (query.executionTime !== undefined) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
    return <Clock className="w-4 h-4 text-gray-400" />;
  };

  const truncateQuery = (query: string, maxLength: number = 80) => {
    if (query.length <= maxLength) return query;
    return query.substring(0, maxLength).trim() + '...';
  };

  if (displayQueries.length === 0) {
    return (
      <div className={clsx('p-4', className)} data-testid={testId}>
        <div className="text-center py-8">
          <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">No query history yet</p>
          <p className="text-gray-400 text-xs mt-1">Run some queries to see them here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('bg-gray-50 h-full flex flex-col', className)} data-testid={testId}>
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">Query History</h4>
          <span className="text-xs text-gray-500">{displayQueries.length} queries</span>
        </div>
      </div>

      {/* Query list */}
      <div className="flex-1 overflow-y-auto">
        <div className="space-y-1 p-2">
          {displayQueries.map((query) => (
            <div
              key={query.id}
              className="group p-3 bg-white rounded-md border hover:shadow-sm transition-all duration-200 cursor-pointer"
              onClick={() => onQuerySelect?.(query)}
            >
              {/* Header with status and timestamp */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(query)}
                  <span className="text-xs text-gray-500">
                    {formatDistanceToNow(query.timestamp, { addSuffix: true })}
                  </span>
                </div>
                {onQueryDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onQueryDelete(query.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 transition-all"
                    title="Delete query"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>

              {/* Query preview */}
              <div className="mb-2">
                <code className="text-xs text-gray-700 bg-gray-50 p-2 rounded block">
                  {truncateQuery(query.query)}
                </code>
              </div>

              {/* Metadata */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-3">
                  {query.executionTime !== undefined && (
                    <div className="flex items-center space-x-1">
                      <Timer className="w-3 h-3" />
                      <span>{formatExecutionTime(query.executionTime)}</span>
                    </div>
                  )}
                  {query.rowCount !== undefined && (
                    <span>{query.rowCount} rows</span>
                  )}
                </div>
                {query.error && (
                  <span className="text-red-600 font-medium">Error</span>
                )}
              </div>

              {/* Error message */}
              {query.error && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  {query.error}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      {queries.length > maxItems && (
        <div className="p-3 border-t bg-white text-center">
          <p className="text-xs text-gray-500">
            Showing {maxItems} of {queries.length} queries
          </p>
        </div>
      )}
    </div>
  );
}