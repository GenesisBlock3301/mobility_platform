import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-[640px] flex-col items-center gap-4 px-4 py-24 text-center">
      <h1 className="font-display text-3xl font-semibold">We could not find that page</h1>
      <p className="text-muted">The role may have been removed, or the link is wrong.</p>
      <Link href="/matches" className="min-h-11 rounded-[10px] bg-accent px-5 py-2.5 font-semibold text-white">
        Back to my matches
      </Link>
    </main>
  );
}
