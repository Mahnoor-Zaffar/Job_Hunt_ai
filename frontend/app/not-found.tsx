export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h1 className="text-4xl font-bold text-muted-foreground mb-4">404</h1>
      <p className="text-muted-foreground mb-6">This page could not be found.</p>
      <a href="/" className="text-primary hover:underline text-sm">
        Go back to Dashboard
      </a>
    </div>
  );
}
