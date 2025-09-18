// Validation utilities
// Basic implementation to resolve import errors

export function validateRequired(value: any, fieldName: string) {
  if (!value) {
    throw new Error(`${fieldName} is required`);
  }
}

export function validateEmail(email: string) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }
}

export function validateId(id: string) {
  if (!id || id.length < 1) {
    throw new Error('Invalid ID');
  }
}

export function validateJobData(data: any) {
  validateRequired(data.title, 'title');
  validateRequired(data.description, 'description');
  validateRequired(data.company, 'company');
}