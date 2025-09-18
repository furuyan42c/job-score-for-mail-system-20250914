"use client";

import { Toaster } from 'sonner';

export function ToasterProvider() {
  return (
    <Toaster
      position="top-right"
      expand
      richColors
      closeButton
      toastOptions={{
        duration: 4000,
        className: 'rounded-lg border',
      }}
    />
  );
}