import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SqlEditor from './index';
import { SqlQueryResult } from '@/types';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => {
  return function MockMonacoEditor({ value, onChange }: any) {
    return (
      <textarea
        data-testid="monaco-editor"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder="SQL Editor"
      />
    );
  };
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock URL.createObjectURL for CSV export
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

describe('SqlEditor', () => {
  const mockQueryResult: SqlQueryResult = {
    columns: [
      { name: 'id', type: 'integer' },
      { name: 'name', type: 'varchar' },
      { name: 'email', type: 'varchar' },
    ],
    rows: [
      { id: 1, name: 'John Doe', email: 'john@example.com' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
    ],
    rowCount: 2,
    executionTime: 150,
    query: 'SELECT id, name, email FROM users',
  };

  const mockOnQueryExecute = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
  });

  it('renders with default props', () => {
    render(<SqlEditor />);

    expect(screen.getByText('SQL Query Editor')).toBeInTheDocument();
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    expect(screen.getByText('Run Query')).toBeInTheDocument();
  });

  it('renders with initial query', () => {
    const initialQuery = 'SELECT * FROM users';
    render(<SqlEditor initialQuery={initialQuery} />);

    expect(screen.getByDisplayValue(initialQuery)).toBeInTheDocument();
  });

  it('updates query when typing in editor', () => {
    render(<SqlEditor />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM jobs' } });

    expect(editor).toHaveValue('SELECT * FROM jobs');
  });

  it('executes query when Run Query button is clicked', async () => {
    mockOnQueryExecute.mockResolvedValue(mockQueryResult);

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(mockOnQueryExecute).toHaveBeenCalledWith('SELECT * FROM users');
    });
  });

  it('shows loading state during query execution', async () => {
    mockOnQueryExecute.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockQueryResult), 100))
    );

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    expect(screen.getByText('Running...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Run Query')).toBeInTheDocument();
    });
  });

  it('prevents non-SELECT queries', async () => {
    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'DELETE FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText('Only SELECT queries are allowed for security reasons.')).toBeInTheDocument();
    });

    expect(mockOnQueryExecute).not.toHaveBeenCalled();
  });

  it('displays query results', async () => {
    mockOnQueryExecute.mockResolvedValue(mockQueryResult);

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText('2 rows')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    });
  });

  it('handles query execution errors', async () => {
    const errorMessage = 'Database connection failed';
    mockOnQueryExecute.mockRejectedValue(new Error(errorMessage));

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText('Query Error')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('saves query history to localStorage', async () => {
    mockOnQueryExecute.mockResolvedValue(mockQueryResult);

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'sql-query-history',
        expect.stringContaining('SELECT * FROM users')
      );
    });
  });

  it('loads query history from localStorage on mount', () => {
    const mockHistory = JSON.stringify([
      {
        id: '1',
        query: 'SELECT * FROM jobs',
        timestamp: new Date().toISOString(),
        executionTime: 200,
        rowCount: 5,
      },
    ]);

    localStorageMock.getItem.mockReturnValue(mockHistory);

    render(<SqlEditor showHistory={true} />);

    expect(localStorageMock.getItem).toHaveBeenCalledWith('sql-query-history');
  });

  it('toggles query templates panel', () => {
    render(<SqlEditor />);

    const templatesButton = screen.getByTitle('Query Templates');
    fireEvent.click(templatesButton);

    expect(screen.getByText('Query Templates')).toBeInTheDocument();
    expect(screen.getByText('Recent Jobs')).toBeInTheDocument();
    expect(screen.getByText('User Registrations')).toBeInTheDocument();
  });

  it('selects template and updates query', () => {
    render(<SqlEditor />);

    const templatesButton = screen.getByTitle('Query Templates');
    fireEvent.click(templatesButton);

    const recentJobsTemplate = screen.getByText('Recent Jobs');
    fireEvent.click(recentJobsTemplate);

    const editor = screen.getByTestId('monaco-editor');
    expect(editor.value).toContain('SELECT');
    expect(editor.value).toContain('FROM jobs');
    expect(editor.value).toContain('posted_at >= NOW()');
  });

  it('disables run button when read-only', () => {
    render(<SqlEditor readOnly={true} />);

    const runButton = screen.getByText('Run Query');
    expect(runButton).toBeDisabled();
  });

  it('exports results to CSV', async () => {
    mockOnQueryExecute.mockResolvedValue(mockQueryResult);

    // Mock document methods
    const mockCreateElement = jest.fn(() => ({
      href: '',
      download: '',
      click: jest.fn(),
    }));
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();

    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;

    render(<SqlEditor onQueryExecute={mockOnQueryExecute} />);

    const editor = screen.getByTestId('monaco-editor');
    fireEvent.change(editor, { target: { value: 'SELECT * FROM users' } });

    const runButton = screen.getByText('Run Query');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText('2 rows')).toBeInTheDocument();
    });

    const exportButton = screen.getByTitle('Export to CSV');
    fireEvent.click(exportButton);

    expect(mockCreateElement).toHaveBeenCalledWith('a');
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('toggles history panel', () => {
    render(<SqlEditor showHistory={true} />);

    const historyButton = screen.getByTitle('Query History');
    fireEvent.click(historyButton);

    // History panel should be visible (though empty in this test)
    expect(screen.getByText('No query history yet')).toBeInTheDocument();
  });
});