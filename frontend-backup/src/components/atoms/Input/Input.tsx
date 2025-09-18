import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { InputProps } from '@/types';

const inputSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-3 text-base'
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      type = 'text',
      placeholder,
      value,
      defaultValue,
      onChange,
      onFocus,
      onBlur,
      disabled = false,
      required = false,
      error,
      label,
      helperText,
      size = 'md',
      icon,
      iconPosition = 'left',
      className,
      'data-testid': testId,
      ...props
    },
    ref
  ) => {
    const hasError = Boolean(error);
    const hasIcon = Boolean(icon);
    const showLabel = Boolean(label);
    const showHelperText = Boolean(helperText || error);

    return (
      <div className={cn('w-full', className)}>
        {/* Label */}
        {showLabel && (
          <label className="block text-sm font-medium text-secondary-700 mb-1">
            {label}
            {required && <span className="text-danger-500 ml-1">*</span>}
          </label>
        )}

        {/* Input Container */}
        <div className="relative">
          {/* Left Icon */}
          {hasIcon && iconPosition === 'left' && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className={cn(
                'text-secondary-400',
                hasError && 'text-danger-400'
              )}>
                {icon}
              </span>
            </div>
          )}

          {/* Input Field */}
          <input
            ref={ref}
            type={type}
            placeholder={placeholder}
            value={value}
            defaultValue={defaultValue}
            onChange={onChange}
            onFocus={onFocus}
            onBlur={onBlur}
            disabled={disabled}
            required={required}
            data-testid={testId}
            className={cn(
              // Base styles
              'block w-full rounded-lg border transition-colors duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:bg-secondary-50 disabled:text-secondary-500 disabled:cursor-not-allowed',
              'placeholder:text-secondary-400',

              // Size styles
              inputSizes[size],

              // Icon padding
              hasIcon && iconPosition === 'left' && 'pl-10',
              hasIcon && iconPosition === 'right' && 'pr-10',

              // State styles
              hasError
                ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500'
                : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-500'
            )}
            {...props}
          />

          {/* Right Icon */}
          {hasIcon && iconPosition === 'right' && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className={cn(
                'text-secondary-400',
                hasError && 'text-danger-400'
              )}>
                {icon}
              </span>
            </div>
          )}
        </div>

        {/* Helper Text / Error */}
        {showHelperText && (
          <p className={cn(
            'mt-1 text-sm',
            hasError ? 'text-danger-600' : 'text-secondary-500'
          )}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';