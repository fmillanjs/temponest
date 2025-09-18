'use client';

import { SessionProvider } from 'next-auth/react';
import { api } from '@/utils/api';
import { Toaster } from '@/components/ui/sonner';

interface AppProviderProps {
  children: React.ReactNode;
}

function AppProviderInner({ children }: AppProviderProps) {
  return (
    <SessionProvider>
      {children}
      <Toaster />
    </SessionProvider>
  );
}

// Use proper tRPC Next.js integration
export const AppProvider = api.withTRPC(AppProviderInner) as React.FC<AppProviderProps>;