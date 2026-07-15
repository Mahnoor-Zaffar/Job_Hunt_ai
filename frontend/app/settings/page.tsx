import { Card } from "@/components/ui";

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="space-y-6 max-w-xl">
        <Card title="Notifications">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" defaultChecked />
              Telegram notifications
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" />
              Email notifications
            </label>
          </div>
        </Card>
        <Card title="Location Preferences">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" defaultChecked />
              Islamabad
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" defaultChecked />
              Rawalpindi
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" defaultChecked />
              Lahore
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="rounded" defaultChecked />
              Remote (Worldwide)
            </label>
          </div>
        </Card>
        <Card title="Scraper Settings">
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Scrape Interval (minutes)</label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-1.5 border rounded text-sm"
                defaultValue={30}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Max Concurrent Scrapers</label>
              <input
                type="number"
                className="w-full mt-1 px-3 py-1.5 border rounded text-sm"
                defaultValue={3}
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
