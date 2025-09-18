import React from 'react';
import { cn } from '@/lib/utils';

interface TypographyProps {
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body' | 'caption' | 'overline';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'inherit';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold';
  align?: 'left' | 'center' | 'right' | 'justify';
  truncate?: boolean;
  children: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

const variantClasses = {
  h1: 'text-4xl md:text-5xl lg:text-6xl font-bold leading-tight',
  h2: 'text-3xl md:text-4xl font-bold leading-tight',
  h3: 'text-2xl md:text-3xl font-semibold leading-snug',
  h4: 'text-xl md:text-2xl font-semibold leading-snug',
  h5: 'text-lg md:text-xl font-medium leading-normal',
  h6: 'text-base md:text-lg font-medium leading-normal',
  body: 'text-base leading-relaxed',
  caption: 'text-sm leading-normal',
  overline: 'text-xs uppercase font-medium tracking-wider leading-normal'
};

const colorClasses = {
  primary: 'text-primary-700',
  secondary: 'text-secondary-700',
  success: 'text-success-700',
  warning: 'text-warning-700',
  danger: 'text-danger-700',
  inherit: 'text-inherit'
};

const weightClasses = {
  light: 'font-light',
  normal: 'font-normal',
  medium: 'font-medium',
  semibold: 'font-semibold',
  bold: 'font-bold'
};

const alignClasses = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
  justify: 'text-justify'
};

const elementMap = {
  h1: 'h1',
  h2: 'h2',
  h3: 'h3',
  h4: 'h4',
  h5: 'h5',
  h6: 'h6',
  body: 'p',
  caption: 'span',
  overline: 'span'
} as const;

export const Typography: React.FC<TypographyProps> = ({
  variant = 'body',
  color = 'secondary',
  weight,
  align = 'left',
  truncate = false,
  children,
  className,
  'data-testid': testId
}) => {
  const Element = elementMap[variant] as keyof JSX.IntrinsicElements;

  return React.createElement(
    Element,
    {
      className: cn(
        // Base variant styles
        variantClasses[variant],

        // Color
        colorClasses[color],

        // Weight override
        weight && weightClasses[weight],

        // Alignment
        alignClasses[align],

        // Truncate
        truncate && 'truncate',

        // Custom className
        className
      ),
      'data-testid': testId
    },
    children
  );
};