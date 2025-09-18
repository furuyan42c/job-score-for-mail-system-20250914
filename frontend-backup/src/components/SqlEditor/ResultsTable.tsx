'use client';

import React, { useState, useMemo } from 'react';
import { ResultsTableProps, SqlColumn } from '@/types';
import { clsx } from 'clsx';
import { Download, ArrowUpDown, ArrowUp, ArrowDown, Timer, Database, Loader2 } from 'lucide-react';

type SortDirection = 'asc' | 'desc' | null;

export default function ResultsTable({
  result,
  loading = false,
  error,
  onExportCsv,
  maxRows = 1000,
  className,
  'data-testid': testId,
}: ResultsTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const sortedData = useMemo(() => {
    if (!result?.rows || !sortColumn || !sortDirection) {
      return result?.rows || [];
    }

    return [...result.rows].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return sortDirection === 'asc' ? -1 : 1;
      if (bValue == null) return sortDirection === 'asc' ? 1 : -1;

      // Handle different data types
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      // Convert to string for comparison
      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();

      if (aStr < bStr) return sortDirection === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [result?.rows, sortColumn, sortDirection]);

  const handleSort = (columnName: string) => {
    if (sortColumn === columnName) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortColumn(columnName);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (columnName: string) => {
    if (sortColumn !== columnName) {
      return <ArrowUpDown className="w-3 h-3 text-gray-400" />;
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="w-3 h-3 text-blue-600" />;
    }
    if (sortDirection === 'desc') {
      return <ArrowDown className="w-3 h-3 text-blue-600" />;
    }
    return <ArrowUpDown className="w-3 h-3 text-gray-400" />;
  };

  const formatCellValue = (value: any, column: SqlColumn) => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">NULL</span>;
    }

    if (typeof value === 'boolean') {
      return (
        <span className={clsx('px-2 py-1 rounded text-xs font-medium', {
          'bg-green-100 text-green-800': value,
          'bg-red-100 text-red-800': !value,
        })}>
          {value ? 'TRUE' : 'FALSE'}
        </span>
      );
    }

    if (typeof value === 'number') {
      return <span className="font-mono">{value.toLocaleString()}</span>;
    }

    if (typeof value === 'string') {
      // Handle dates
      if (column.type.toLowerCase().includes('date') || column.type.toLowerCase().includes('time')) {
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            return (
              <span className="text-blue-700 font-mono">
                {date.toLocaleString()}
              </span>
            );
          }
        } catch {
          // Not a valid date, treat as regular string
        }
      }

      // Truncate long strings
      if (value.length > 100) {
        return (
          <span title={value} className="cursor-help">
            {value.substring(0, 100)}...
          </span>
        );
      }
    }

    return String(value);
  };

  const displayRows = sortedData.slice(0, maxRows);
  const hasMoreRows = sortedData.length > maxRows;

  if (loading) {
    return (
      <div className={clsx('p-8 text-center', className)} data-testid={testId}>
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p className="text-gray-600">Executing query...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx('p-4', className)} data-testid={testId}>
        {/* Error is handled in parent component */}
      </div>
    );
  }

  if (!result) {
    return (
      <div className={clsx('p-8 text-center', className)} data-testid={testId}>
        <Database className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">Run a query to see results here</p>
      </div>
    );
  }

  return (
    <div className={clsx('bg-white', className)} data-testid={testId}>
      {/* Results header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-gray-600" />
            <span className="text-sm text-gray-900 font-medium">
              {result.rowCount.toLocaleString()} rows
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Timer className="w-4 h-4 text-gray-600" />
            <span className="text-sm text-gray-600">
              {result.executionTime < 1000
                ? `${result.executionTime}ms`
                : `${(result.executionTime / 1000).toFixed(2)}s`
              }
            </span>
          </div>
        </div>
        {onExportCsv && result.rows.length > 0 && (
          <button
            onClick={onExportCsv}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
        )}
      </div>

      {/* Results table */}
      {result.rows.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-gray-500">No results found</p>
        </div>
      ) : (
        <div className="overflow-auto max-h-96">
          <table className="w-full">
            {/* Table header */}
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {result.columns.map((column) => (
                  <th
                    key={column.name}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider border-b cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort(column.name)}
                  >
                    <div className="flex items-center space-x-2">
                      <span>{column.name}</span>
                      {getSortIcon(column.name)}
                    </div>
                    <div className="text-xs text-gray-500 normal-case font-normal mt-1">
                      {column.type}
                      {column.nullable && ' (nullable)'}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>

            {/* Table body */}
            <tbody className="bg-white divide-y divide-gray-200">
              {displayRows.map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  {result.columns.map((column) => (
                    <td
                      key={column.name}
                      className="px-4 py-3 text-sm text-gray-900 border-b"
                    >
                      {formatCellValue(row[column.name], column)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer with pagination info */}
      {hasMoreRows && (
        <div className="p-4 border-t bg-gray-50 text-center">
          <p className="text-sm text-gray-600">
            Showing first {maxRows.toLocaleString()} of {result.rowCount.toLocaleString()} rows
          </p>
        </div>
      )}
    </div>
  );
}