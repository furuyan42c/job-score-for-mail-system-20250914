import React, { useState, useEffect } from 'react';
import { cn, debounce } from '@/lib/utils';
import { Input, Button } from '@/components/atoms';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  onClear?: () => void;
  debounceMs?: number;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showSearchButton?: boolean;
  showClearButton?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  value = '',
  onChange,
  onSearch,
  onClear,
  debounceMs = 300,
  disabled = false,
  size = 'md',
  showSearchButton = true,
  showClearButton = true,
  className,
  'data-testid': testId
}) => {
  const [internalValue, setInternalValue] = useState(value);

  // Debounced search function
  const debouncedOnChange = React.useMemo(
    () => onChange ? debounce(onChange, debounceMs) : undefined,
    [onChange, debounceMs]
  );

  // Update internal value when external value changes
  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  // Handle input change
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setInternalValue(newValue);
    debouncedOnChange?.(newValue);
  };

  // Handle search button click
  const handleSearch = () => {
    onSearch?.(internalValue);
  };

  // Handle clear
  const handleClear = () => {
    setInternalValue('');
    onChange?.('');
    onClear?.();
  };

  // Handle enter key press
  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleSearch();
    }
  };

  const hasValue = Boolean(internalValue);

  return (
    <div className={cn('flex items-center gap-2', className)} data-testid={testId}>
      {/* Search Input */}
      <div className="flex-1">
        <Input
          type="search"
          placeholder={placeholder}
          value={internalValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          size={size}
          icon={<Search />}
          iconPosition="left"
          data-testid={`${testId}-input`}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1">
        {/* Clear Button */}
        {showClearButton && hasValue && (
          <Button
            variant="ghost"
            size={size}
            onClick={handleClear}
            disabled={disabled}
            icon={<X />}
            data-testid={`${testId}-clear`}
            className="px-2"
          />
        )}

        {/* Search Button */}
        {showSearchButton && (
          <Button
            variant="primary"
            size={size}
            onClick={handleSearch}
            disabled={disabled}
            icon={<Search />}
            data-testid={`${testId}-search`}
          >
            Search
          </Button>
        )}
      </div>
    </div>
  );
};