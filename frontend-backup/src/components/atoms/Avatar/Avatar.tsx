import React from 'react';
import { cn } from '@/lib/utils';
import { User } from 'lucide-react';

interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  shape?: 'circle' | 'square';
  className?: string;
  'data-testid'?: string;
}

const sizeClasses = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
  '2xl': 'w-20 h-20 text-2xl'
};

const iconSizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
  '2xl': 'w-10 h-10'
};

export const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  name,
  size = 'md',
  shape = 'circle',
  className,
  'data-testid': testId
}) => {
  const [imageError, setImageError] = React.useState(false);

  // Get initials from name
  const getInitials = (name?: string): string => {
    if (!name) return '';
    return name
      .split(' ')
      .map(part => part.charAt(0))
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  const initials = getInitials(name);
  const showImage = src && !imageError;
  const showInitials = !showImage && initials;
  const showIcon = !showImage && !showInitials;

  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center bg-secondary-100 overflow-hidden',
        sizeClasses[size],
        shape === 'circle' ? 'rounded-full' : 'rounded-lg',
        className
      )}
      data-testid={testId}
    >
      {showImage && (
        <img
          src={src}
          alt={alt || name || 'Avatar'}
          onError={() => setImageError(true)}
          className="w-full h-full object-cover"
        />
      )}

      {showInitials && (
        <span className="font-medium text-secondary-700 select-none">
          {initials}
        </span>
      )}

      {showIcon && (
        <User className={cn('text-secondary-400', iconSizeClasses[size])} />
      )}
    </div>
  );
};