import type { Metadata } from "next";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Hunting AI",
  description: "AI-powered Job Intelligence & Application Automation Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground font-sans antialiased">
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
            <div className="flex h-14 items-center px-6 gap-6">
              <a href="/" className="font-bold text-lg text-primary">
                Job Hunting AI
              </a>
              <nav className="flex gap-4 text-sm text-muted-foreground flex-1">
                <a href="/" className="hover:text-foreground transition-colors">Dashboard</a>
                <a href="/jobs" className="hover:text-foreground transition-colors">Jobs</a>
                <a href="/companies" className="hover:text-foreground transition-colors">Companies</a>
                <a href="/applications" className="hover:text-foreground transition-colors">Applications</a>
                <a href="/resume" className="hover:text-foreground transition-colors">Resume</a>
                <a href="/settings" className="hover:text-foreground transition-colors">Settings</a>
              </nav>
              <ThemeToggle />
            </div>
          </header>
          <main className="flex-1 px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
