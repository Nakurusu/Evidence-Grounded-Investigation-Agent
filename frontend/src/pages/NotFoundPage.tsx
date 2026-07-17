import { Link } from "react-router-dom";
import { ArrowLeft, Search } from "lucide-react";

export function NotFoundPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-24">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-muted mb-6">
        <Search className="h-7 w-7 text-accent" />
      </div>
      <h1 className="mb-2 text-2xl font-bold text-foreground">
        Page not found
      </h1>
      <p className="mb-8 max-w-sm text-center text-sm text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-colors hover:opacity-90"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Home
      </Link>
    </div>
  );
}
