"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { api, CareerProfile, NotificationPreferences } from "@/lib/api";

const DEFAULT_PREFS: NotificationPreferences = {
  telegram_enabled: true,
  email_enabled: false,
  notify_on_match: true,
  notify_on_new_jobs: true,
  min_match_score: 0.6,
  alert_skills: "JavaScript, Python, AI/ML, DevOps, Docker, TypeScript, Node.js, Express.js",
  alert_min_score: 0.3,
  alert_email: "",
  digest_enabled: false,
};

const DEFAULT_PROFILE: CareerProfile = {
  id: "",
  user_id: "",
  skills: [],
  experience_level: "mid",
  years_experience: 0,
  target_roles: [],
  preferred_locations: [],
  remote_preference: "no_preference",
  preferred_salary_min: null,
  preferred_companies: [],
  tech_stack: [],
  learning_goals: [],
  resume_text: null,
};

type TagEditorProps = {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
};

function TagEditor({ label, tags, onChange, placeholder }: TagEditorProps) {
  const [input, setInput] = useState("");
  function addTag() {
    const val = input.trim();
    if (val && !tags.includes(val)) {
      onChange([...tags, val]);
    }
    setInput("");
  }
  function removeTag(tag: string) {
    onChange(tags.filter((t) => t !== tag));
  }
  return (
    <div>
      <label className="text-sm font-medium block mb-1">{label}</label>
      <div className="flex gap-1.5 flex-wrap mb-1.5">
        {tags.map((t) => (
          <span key={t} className="text-xs bg-secondary px-2 py-0.5 rounded flex items-center gap-1">
            {t}
            <button onClick={() => removeTag(t)} className="text-muted-foreground hover:text-foreground">×</button>
          </span>
        ))}
      </div>
      <div className="flex gap-1">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTag(); } }}
          className="flex-1 px-3 py-1.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
          placeholder={placeholder || `Add ${label.toLowerCase()}...`}
        />
        <button onClick={addTag} className="px-2 py-1 text-xs bg-secondary rounded-lg hover:bg-secondary/80">+</button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<NotificationPreferences>(DEFAULT_PREFS);
  const [profile, setProfile] = useState<CareerProfile>(DEFAULT_PROFILE);
  const [saved, setSaved] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [profileTab, setProfileTab] = useState<"profile" | "notifications">("profile");

  useEffect(() => {
    Promise.all([
      api.notifications.getPreferences().catch(() => DEFAULT_PREFS),
      api.profile.get().catch(() => null),
    ]).then(([prefData, profileData]) => {
      setPrefs({ ...DEFAULT_PREFS, ...prefData });
      if (profileData) setProfile(profileData);
      setLoading(false);
    });
  }, []);

  async function savePrefs() {
    setSaved(false);
    await api.notifications.updatePreferences(prefs);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function saveProfile() {
    setProfileSaved(false);
    const data: Record<string, any> = {};
    for (const [key, val] of Object.entries(profile)) {
      if (key !== "id" && key !== "user_id") data[key] = val;
    }
    await api.profile.update(data);
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 2000);
  }

  async function regenerateSkills() {
    try {
      const updated = await api.profile.regenerate();
      setProfile(updated);
    } catch (e: any) {
      setSyncResult("Error: " + e.message);
    }
  }

  async function syncCompanies() {
    setSyncResult("Syncing...");
    try {
      const itResult = await api.companies.syncItCompanies();
      setSyncResult(itResult.message);
    } catch (e: any) {
      setSyncResult("Error: " + e.message);
    }
  }

  async function refreshEmailVerification() {
    try {
      const status = await api.companies.emailVerificationStatus();
      setSyncResult(`Verified: ${status.verified} / ${status.total} companies`);
    } catch (e: any) {
      setSyncResult("Error: " + e.message);
    }
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setProfileTab("profile")}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${profileTab === "profile" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}
        >
          Career Profile
        </button>
        <button
          onClick={() => setProfileTab("notifications")}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${profileTab === "notifications" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/70"}`}
        >
          Notifications & Sync
        </button>
      </div>

      {profileTab === "profile" ? (
        <div className="space-y-6 max-w-xl">
          <div className="flex justify-end">
            <button
              onClick={saveProfile}
              className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              {profileSaved ? "✓ Saved" : "Save Profile"}
            </button>
          </div>

          <Card title="Skills & Experience">
            <div className="space-y-4">
              <TagEditor label="Skills" tags={profile.skills} onChange={(s) => setProfile({ ...profile, skills: s })} placeholder="Python, FastAPI, Docker..." />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium block mb-1">Experience Level</label>
                  <select value={profile.experience_level} onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background">
                    <option value="junior">Junior</option>
                    <option value="mid">Mid</option>
                    <option value="senior">Senior</option>
                    <option value="lead">Lead</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1">Years Experience</label>
                  <input type="number" value={profile.years_experience} onChange={(e) => setProfile({ ...profile, years_experience: parseInt(e.target.value) || 0 })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background" min={0} max={50} />
                </div>
              </div>
            </div>
          </Card>

          <Card title="Target Roles & Tech Stack">
            <div className="space-y-4">
              <TagEditor label="Target Roles" tags={profile.target_roles} onChange={(r) => setProfile({ ...profile, target_roles: r })} placeholder="Backend Engineer, Python Developer..." />
              <TagEditor label="Tech Stack" tags={profile.tech_stack} onChange={(t) => setProfile({ ...profile, tech_stack: t })} placeholder="Python, FastAPI, PostgreSQL..." />
              <TagEditor label="Learning Goals" tags={profile.learning_goals} onChange={(l) => setProfile({ ...profile, learning_goals: l })} placeholder="Docker, AWS, Kubernetes..." />
            </div>
          </Card>

          <Card title="Preferences">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium block mb-1">Remote Preference</label>
                  <select value={profile.remote_preference} onChange={(e) => setProfile({ ...profile, remote_preference: e.target.value })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background">
                    <option value="no_preference">No Preference</option>
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="onsite">On-site</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1">Expected Salary (USD)</label>
                  <input type="number" value={profile.preferred_salary_min || ""} onChange={(e) => setProfile({ ...profile, preferred_salary_min: e.target.value ? parseFloat(e.target.value) : null })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background" min={0} placeholder="100000" />
                </div>
              </div>
              <TagEditor label="Preferred Locations" tags={profile.preferred_locations} onChange={(l) => setProfile({ ...profile, preferred_locations: l })} placeholder="Islamabad, Lahore..." />
              <TagEditor label="Preferred Companies" tags={profile.preferred_companies} onChange={(c) => setProfile({ ...profile, preferred_companies: c })} placeholder="Google, Careem, Turing..." />
            </div>
          </Card>

          <Card title="Resume">
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">Paste your full resume text below. The system uses it to match job descriptions.</p>
              <textarea
                value={profile.resume_text || ""}
                onChange={(e) => setProfile({ ...profile, resume_text: e.target.value })}
                className="w-full h-40 px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Paste your resume here..."
              />
              <button onClick={regenerateSkills} className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors">
                Regenerate Skills from Resume
              </button>
              {syncResult && <p className="text-xs text-muted-foreground">{syncResult}</p>}
            </div>
          </Card>
        </div>
      ) : (
        <div className="space-y-6 max-w-xl">
          <div className="flex justify-end">
            <button
              onClick={savePrefs}
              className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              {saved ? "✓ Saved" : "Save Changes"}
            </button>
          </div>

          <Card title="Skills & Alerts">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Your Skills (comma-separated)</label>
                <p className="text-xs text-muted-foreground mb-2">Jobs matching these skills at watched companies will trigger alerts.</p>
                <input type="text" value={prefs.alert_skills} onChange={(e) => setPrefs({ ...prefs, alert_skills: e.target.value })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20" placeholder="Python, JavaScript, React, Node.js, Docker..." />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">Minimum Match Score: {prefs.alert_min_score}</label>
                <input type="range" min="0.1" max="1.0" step="0.1" value={prefs.alert_min_score} onChange={(e) => setPrefs({ ...prefs, alert_min_score: parseFloat(e.target.value) })} className="w-full" />
                <div className="flex justify-between text-[10px] text-muted-foreground mt-0.5">
                  <span>Loose (0.1)</span>
                  <span>Strict (1.0)</span>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Notifications">
            <div className="space-y-4">
              <label className="flex items-center justify-between">
                <span className="text-sm">Telegram notifications</span>
                <input type="checkbox" checked={prefs.telegram_enabled} onChange={(e) => setPrefs({ ...prefs, telegram_enabled: e.target.checked })} className="w-4 h-4 rounded" />
              </label>
              <label className="flex items-center justify-between">
                <div>
                  <span className="text-sm">Email notifications</span>
                  <p className="text-xs text-muted-foreground">Requires SMTP configuration</p>
                </div>
                <input type="checkbox" checked={prefs.email_enabled} onChange={(e) => setPrefs({ ...prefs, email_enabled: e.target.checked })} className="w-4 h-4 rounded" />
              </label>
              <div>
                <label className="text-sm font-medium block mb-1">Email address for alerts</label>
                <input type="email" value={prefs.alert_email} onChange={(e) => setPrefs({ ...prefs, alert_email: e.target.value })} className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20" placeholder="you@example.com" />
              </div>
              <label className="flex items-center justify-between">
                <div>
                  <span className="text-sm">Daily email digest</span>
                  <p className="text-xs text-muted-foreground">Bundle all alerts into one daily email</p>
                </div>
                <input type="checkbox" checked={prefs.digest_enabled} onChange={(e) => setPrefs({ ...prefs, digest_enabled: e.target.checked })} className="w-4 h-4 rounded" />
              </label>
              <label className="flex items-center justify-between">
                <span className="text-sm">Notify on job match</span>
                <input type="checkbox" checked={prefs.notify_on_match} onChange={(e) => setPrefs({ ...prefs, notify_on_match: e.target.checked })} className="w-4 h-4 rounded" />
              </label>
              <label className="flex items-center justify-between">
                <span className="text-sm">Notify on new jobs</span>
                <input type="checkbox" checked={prefs.notify_on_new_jobs} onChange={(e) => setPrefs({ ...prefs, notify_on_new_jobs: e.target.checked })} className="w-4 h-4 rounded" />
              </label>
            </div>
          </Card>

          <Card title="Company Sync">
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">Import curated company lists into the database for email verification and job alerts.</p>
              <div className="flex gap-2">
                <button onClick={syncCompanies} className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors">
                  Sync IT Companies & Startups
                </button>
                <button onClick={refreshEmailVerification} className="px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors">
                  Check Verification Status
                </button>
              </div>
              {syncResult && <p className="text-xs text-muted-foreground">{syncResult}</p>}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
