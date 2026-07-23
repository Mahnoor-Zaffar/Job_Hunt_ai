import { ItCompaniesFinder } from "@/components/it-companies";

export default function ItCompaniesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">IT Companies — Pakistan</h1>
        <p className="text-sm text-muted-foreground mt-1">
          50+ mid-sized software houses and IT services firms. Load the list, verify HR emails, and send personalized cold emails.
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium">How it works</h3>
            <div className="grid grid-cols-3 gap-4 mt-3">
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">1️⃣</span>
                <span>Load 50 curated mid-sized IT companies with guessed HR emails</span>
              </div>
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">2️⃣</span>
                <span>Verify emails in background — detects valid/invalid with confidence badges</span>
              </div>
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">3️⃣</span>
                <span>AI-personalize cold emails with problem-solution framing per company tier</span>
              </div>
            </div>
          </div>

          <ItCompaniesFinder />
        </div>
      </div>
    </div>
  );
}
