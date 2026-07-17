import type { Metadata } from "next";
import AppLayout from "@/components/app-layout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Hunting AI",
  description: "AI-powered Job Intelligence & Application Automation Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
