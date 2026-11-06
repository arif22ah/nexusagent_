import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'NexusAgent Platform',
  description: 'Enterprise Dynamic Agentic AI Control Plane',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased bg-background text-slate-100">{children}</body>
    </html>
  );
}
