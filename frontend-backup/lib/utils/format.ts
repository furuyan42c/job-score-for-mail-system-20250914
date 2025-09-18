// Format utility functions
// Basic implementation to resolve import errors

export function formatSalary(salary: {
  min?: number;
  max?: number;
  currency?: string;
  period?: string;
}): string {
  const { min, max, currency = 'USD', period = 'year' } = salary;

  if (min && max) {
    return `${currency} ${min.toLocaleString()} - ${max.toLocaleString()} per ${period}`;
  } else if (min) {
    return `${currency} ${min.toLocaleString()}+ per ${period}`;
  } else if (max) {
    return `Up to ${currency} ${max.toLocaleString()} per ${period}`;
  }

  return 'Salary not disclosed';
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatExperience(level: string): string {
  const levels: Record<string, string> = {
    'entry': 'Entry Level',
    'junior': 'Junior Level',
    'mid': 'Mid Level',
    'senior': 'Senior Level',
    'lead': 'Lead Level',
    'principal': 'Principal Level'
  };

  return levels[level] || level;
}