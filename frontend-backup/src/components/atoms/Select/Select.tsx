import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { SelectProps, SelectOption } from '@/types';
import { ChevronDown, X, Search, Check } from 'lucide-react';

export const Select: React.FC<SelectProps> = ({
  options,
  value,
  defaultValue,
  onChange,
  placeholder = 'Select option...',
  disabled = false,
  required = false,
  error,
  label,
  helperText,
  multiple = false,
  searchable = false,
  clearable = false,
  size = 'md',
  className,
  'data-testid': testId
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [internalValue, setInternalValue] = useState<string | string[]>(
    value || defaultValue || (multiple ? [] : '')
  );

  const selectRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const hasError = Boolean(error);
  const showLabel = Boolean(label);
  const showHelperText = Boolean(helperText || error);

  // Filter options based on search term
  const filteredOptions = searchable && searchTerm
    ? options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (option.description && option.description.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : options;

  // Get display value
  const getDisplayValue = () => {
    if (multiple) {
      const selectedOptions = options.filter(option =>
        Array.isArray(internalValue) && internalValue.includes(option.value)
      );
      return selectedOptions.length > 0
        ? `${selectedOptions.length} selected`
        : placeholder;
    } else {
      const selectedOption = options.find(option => option.value === internalValue);
      return selectedOption ? selectedOption.label : placeholder;
    }
  };

  // Handle option selection
  const handleOptionSelect = (optionValue: string) => {
    let newValue: string | string[];

    if (multiple) {
      const currentArray = Array.isArray(internalValue) ? internalValue : [];
      if (currentArray.includes(optionValue)) {
        newValue = currentArray.filter(v => v !== optionValue);
      } else {
        newValue = [...currentArray, optionValue];
      }
    } else {
      newValue = optionValue;
      setIsOpen(false);
    }

    setInternalValue(newValue);
    onChange?.(newValue);
  };

  // Handle clear
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newValue = multiple ? [] : '';
    setInternalValue(newValue);
    onChange?.(newValue);
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  const isSelected = (optionValue: string) => {
    if (multiple) {
      return Array.isArray(internalValue) && internalValue.includes(optionValue);
    }
    return internalValue === optionValue;
  };

  const hasValue = multiple
    ? Array.isArray(internalValue) && internalValue.length > 0
    : Boolean(internalValue);

  return (
    <div className={cn('w-full', className)} ref={selectRef}>
      {/* Label */}
      {showLabel && (
        <label className="block text-sm font-medium text-secondary-700 mb-1">
          {label}
          {required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}

      {/* Select Button */}
      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          data-testid={testId}
          className={cn(
            // Base styles
            'relative w-full rounded-lg border text-left transition-colors duration-200',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            'disabled:bg-secondary-50 disabled:text-secondary-500 disabled:cursor-not-allowed',

            // Size styles
            sizeClasses[size],

            // State styles
            hasError
              ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500'
              : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-500',

            // Open state
            isOpen && !hasError && 'border-primary-500 ring-2 ring-primary-500'
          )}
        >
          <span className={cn(
            'block truncate',
            !hasValue && 'text-secondary-400'
          )}>
            {getDisplayValue()}
          </span>

          <span className="absolute inset-y-0 right-0 flex items-center pr-2 space-x-1">
            {clearable && hasValue && !disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 hover:bg-secondary-100 rounded"
              >
                <X className="w-4 h-4 text-secondary-400" />
              </button>
            )}
            <ChevronDown
              className={cn(
                'w-4 h-4 text-secondary-400 transition-transform duration-200',
                isOpen && 'transform rotate-180'
              )}
            />
          </span>
        </button>

        {/* Dropdown */}
        {isOpen && (
          <div className={cn(
            'absolute z-50 w-full mt-1 bg-white border border-secondary-200 rounded-lg shadow-lg',
            'max-h-60 overflow-auto'
          )}>
            {/* Search Input */}
            {searchable && (
              <div className="p-2 border-b border-secondary-100">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-secondary-400" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search options..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 text-sm border border-secondary-200 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            )}

            {/* Options */}
            <div className="py-1">
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-secondary-500">
                  No options found
                </div>
              ) : (
                filteredOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => !option.disabled && handleOptionSelect(option.value)}
                    disabled={option.disabled}
                    className={cn(
                      'w-full px-3 py-2 text-left text-sm transition-colors duration-150',
                      'hover:bg-secondary-50 focus:outline-none focus:bg-secondary-50',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      isSelected(option.value) && 'bg-primary-50 text-primary-700'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium">{option.label}</div>
                        {option.description && (
                          <div className="text-xs text-secondary-500 mt-0.5">
                            {option.description}
                          </div>
                        )}
                      </div>
                      {isSelected(option.value) && (
                        <Check className="w-4 h-4 text-primary-600" />
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
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
};