import { Card } from "@/components/ui";

export default function CompaniesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Companies</h1>
      <Card>
        <p className="text-sm text-muted-foreground py-8 text-center">
          Companies will appear here as jobs are scraped. Add companies to your watchlist to
          receive notifications when they post new roles.
        </p>
      </Card>
    </div>
  );
}
