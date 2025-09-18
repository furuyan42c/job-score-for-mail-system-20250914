import React from 'react';
import { cn } from '@/lib/utils';
import { DeviceFrameProps } from './types';

export const DeviceFrame: React.FC<DeviceFrameProps> = ({
  children,
  device,
  className
}) => {
  const frameStyles = {
    desktop: 'max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden',
    mobile: 'max-w-sm mx-auto bg-white shadow-lg rounded-[2.5rem] overflow-hidden border-8 border-gray-800 relative'
  };

  const mobileFrameDecorations = device === 'mobile' && (
    <>
      {/* Mobile frame top */}
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1/3 h-1 bg-gray-600 rounded-b-lg z-10"></div>
      {/* Mobile frame home indicator */}
      <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 w-1/3 h-1 bg-gray-600 rounded-full z-10"></div>
    </>
  );

  const contentStyles = {
    desktop: 'p-0',
    mobile: 'p-2 min-h-[600px] bg-gray-50'
  };

  return (
    <div className={cn(frameStyles[device], className)}>
      {mobileFrameDecorations}
      <div className={contentStyles[device]}>
        {children}
      </div>
    </div>
  );
};