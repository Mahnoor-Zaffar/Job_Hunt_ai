import { AiAssistantPanel } from "@/components/ai-assistant-panel";
import { Card } from "@/components/ui";

async function getJob(id: string) {
  try {
    const res = await fetch(`http://localhost:8000/api/v1/jobs/${id}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

async function getSimilarJobs(id: string) {
  try {
    const res = await fetch(`http://localhost:8000/api/v1/jobs/${id}/similar?per_page=6`, { next: { revalidate: 60 } });
    if (!res.ok) return { items: [] };
    return await res.json();
  } catch { return { items: [] }; }
}

function formatSalary(min: number | null, max: number | null, currency: string | null) {
  if (!min) return null;
  const cur = currency || "$";
  if (max) return `${cur}${min.toLocaleString()} – ${cur}${max.toLocaleString()}`;
  return `${cur}${min.toLocaleString()}`;
}

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await getJob(id);

  if (!job) {
    return (
      <div>
        <a href="/jobs" className="text-sm text-primary hover:underline mb-4 inline-block">← Back to Jobs</a>
        <Card><p className="text-sm text-muted-foreground py-8 text-center">Job not found.</p></Card>
      </div>
    );
  }

  const similar = await getSimilarJobs(id);
  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);

  return (
    <div>
      <a href="/jobs" className="text-sm text-primary hover:underline mb-4 inline-block">← Back to Jobs</a>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">{job.title}</h1>
            <p className="text-lg text-muted-foreground">{job.company}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            {job.apply_url && (
              <a href={job.apply_url} target="_blank" rel="noopener" className="px-4 py-2 bg-primary text-primary-foreground text-sm rounded hover:bg-primary/90 transition-colors">
                Apply Now →
              </a>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-3 flex-wrap text-sm">
          <span className="text-muted-foreground">{job.location}</span>
          {job.city && <span className="text-muted-foreground">· {job.city}</span>}
          {salary && <span className="text-primary font-medium">· {salary}</span>}
          <span className="capitalize bg-muted px-2 py-0.5 rounded text-xs">{job.source}</span>
          {job.remote_type && job.remote_type !== "onsite" && (
            <span className="capitalize bg-muted px-2 py-0.5 rounded text-xs">{job.remote_type}</span>
          )}
          {job.employment_type && (
            <span className="capitalize bg-muted px-2 py-0.5 rounded text-xs">{job.employment_type.replace("_", " ")}</span>
          )}
          {job.experience_level && (
            <span className="capitalize bg-muted px-2 py-0.5 rounded text-xs">{job.experience_level}</span>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Skills */}
          {(job.skills as string[])?.length > 0 && (
            <Card title="Skills">
              <div className="flex gap-1.5 flex-wrap">
                {(job.skills as string[]).map((s: string) => (
                  <span key={s} className="text-xs bg-muted px-2.5 py-1 rounded-full">{s}</span>
                ))}
              </div>
            </Card>
          )}

          {/* Description */}
          {job.description && (
            <Card title="Description">
              <div className="text-sm leading-relaxed whitespace-pre-line text-muted-foreground max-h-[600px] overflow-y-auto">
                {String(job.description).replace(/<[^>]+>/g, "").substring(0, 5000)}
              </div>
            </Card>
          )}

          {/* Requirements */}
          {job.requirements && (
            <Card title="Requirements">
              <div className="text-sm leading-relaxed whitespace-pre-line text-muted-foreground">
                {String(job.requirements)}
              </div>
            </Card>
          )}

          {/* AI Actions */}
          <Card title="AI Assistant">
            <AiAssistantPanel jobId={id} />
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <h3 className="font-semibold text-sm mb-2">Job Details</h3>
            <dl className="space-y-2 text-sm">
              {job.company && <div><dt className="text-muted-foreground">Company</dt><dd>{String(job.company)}</dd></div>}
              {job.location && <div><dt className="text-muted-foreground">Location</dt><dd>{String(job.location)}</dd></div>}
              {job.city && <div><dt className="text-muted-foreground">City</dt><dd>{String(job.city)}</dd></div>}
              {job.source && <div><dt className="text-muted-foreground">Source</dt><dd className="capitalize">{String(job.source)}</dd></div>}
              {job.experience_level && <div><dt className="text-muted-foreground">Level</dt><dd className="capitalize">{String(job.experience_level)}</dd></div>}
              {job.employment_type && <div><dt className="text-muted-foreground">Type</dt><dd className="capitalize">{String(job.employment_type)}</dd></div>}
              {salary && <div><dt className="text-muted-foreground">Salary</dt><dd className="text-primary">{salary}</dd></div>}
              {job.posted_at && <div><dt className="text-muted-foreground">Posted</dt><dd>{new Date(String(job.posted_at)).toLocaleDateString()}</dd></div>}
            </dl>
          </Card>

          {/* Similar Jobs */}
          {similar.items?.length > 0 && (
            <Card title="Similar Jobs">
              <div className="space-y-2">
                {similar.items.filter((j: Record<string, unknown>) => j.id !== id).slice(0, 5).map((j: Record<string, unknown>) => (
                  <a key={String(j.id)} href={`/jobs/${j.id}`} className="block text-sm hover:text-primary transition-colors">
                    <span className="font-medium truncate block">{String(j.title)}</span>
                    <span className="text-xs text-muted-foreground">{String(j.company)}</span>
                  </a>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
