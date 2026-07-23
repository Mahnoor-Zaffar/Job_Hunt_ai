import { StartupFinder } from "@/components/startup-finder";

export default function StartupsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pakistan Startups</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Discover software startups in Pakistan, find remote hiring opportunities, and get HR emails to send applications.
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium">How it works</h3>
            <div className="grid grid-cols-3 gap-4 mt-3">
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">1️⃣</span>
                <span>Searches 30+ queries across Google for Pakistani software startups</span>
              </div>
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">2️⃣</span>
                <span>Visits each company website to detect full-stack/backend roles and remote opportunities</span>
              </div>
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span className="text-base">3️⃣</span>
                <span>Finds HR emails (hr@, careers@) and pre-builds application email subjects</span>
              </div>
            </div>
          </div>

          <StartupFinder />
        </div>
      </div>
    </div>
  );
}
