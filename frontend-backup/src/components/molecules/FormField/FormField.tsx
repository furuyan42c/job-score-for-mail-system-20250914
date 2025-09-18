import React from 'react';
import { cn } from '@/lib/utils';
import { Input, Select, Typography } from '@/components/atoms';
import { InputProps, SelectProps } from '@/types';

interface BaseFormFieldProps {
  label?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  className?: string;
  'data-testid'?: string;
}

interface InputFormFieldProps extends BaseFormFieldProps {
  type: 'input';
  inputProps: Omit<InputProps, 'label' | 'error' | 'helperText' | 'required'>;
}

interface SelectFormFieldProps extends BaseFormFieldProps {
  type: 'select';
  selectProps: Omit<SelectProps, 'label' | 'error' | 'helperText' | 'required'>;
}

interface TextareaFormFieldProps extends BaseFormFieldProps {
  type: 'textarea';
  textareaProps: React.TextareaHTMLAttributes<HTMLTextAreaElement>;
}

type FormFieldProps = InputFormFieldProps | SelectFormFieldProps | TextareaFormFieldProps;

export const FormField: React.FC<FormFieldProps> = (props) => {
  const { label, required = false, error, helperText, className, 'data-testid': testId } = props;

  const hasError = Boolean(error);
  const showLabel = Boolean(label);
  const showHelperText = Boolean(helperText || error);

  const renderField = () => {
    switch (props.type) {
      case 'input':
        return (
          <Input
            {...props.inputProps}
            required={required}
            error={error}
            data-testid={`${testId}-input`}
          />
        );

      case 'select':
        return (
          <Select
            {...props.selectProps}
            required={required}
            error={error}
            data-testid={`${testId}-select`}
          />
        );

      case 'textarea':
        return (
          <textarea
            {...props.textareaProps}
            required={required}
            data-testid={`${testId}-textarea`}
            className={cn(
              // Base styles
              'block w-full rounded-lg border transition-colors duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:bg-secondary-50 disabled:text-secondary-500 disabled:cursor-not-allowed',
              'placeholder:text-secondary-400',
              'px-3 py-2 text-sm min-h-[80px] resize-vertical',

              // State styles
              hasError
                ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500'
                : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-500',

              props.textareaProps.className
            )}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className={cn('w-full', className)} data-testid={testId}>
      {/* Label */}
      {showLabel && (
        <label className="block text-sm font-medium text-secondary-700 mb-1">
          {label}
          {required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}

      {/* Field */}
      {renderField()}

      {/* Helper Text / Error */}
      {showHelperText && (
        <Typography
          variant="caption"
          color={hasError ? 'danger' : 'secondary'}
          className="mt-1"
        >
          {error || helperText}
        </Typography>
      )}
    </div>
  );
};