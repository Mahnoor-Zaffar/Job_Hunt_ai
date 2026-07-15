import { Card } from "@/components/ui";

export default function ApplicationsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Applications</h1>
      <Card>
        <p className="text-sm text-muted-foreground py-8 text-center">
          Track your job applications here. Apply to jobs to see your application status,
          match scores, and interview pipeline.
        </p>
      </Card>
    </div>
  );
}
