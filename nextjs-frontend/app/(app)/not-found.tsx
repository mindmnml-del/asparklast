import Link from "next/link";

export default function AppNotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <h2 className="text-xl font-semibold">Page not found</h2>
      <p className="text-muted-foreground text-sm">
        The page you are looking for does not exist.
      </p>
      <Link
        href="/generate"
        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition"
      >
        Go to Studio
      </Link>
    </div>
  );
}
