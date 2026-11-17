"use client";

import { AlertIcon } from "@/components/icons";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex max-w-[640px] flex-col items-center gap-4 px-4 py-24 text-center">
      <AlertIcon className="size-10 text-warn" />
      <h1 className="font-display text-3xl font-semibold">The service is temporarily unavailable</h1>
      <p className="text-muted">Nothing you entered was lost. Wait a moment, then try again.</p>
      <button
        type="button"
        onClick={reset}
        className="min-h-11 rounded-[10px] bg-accent px-5 font-semibold text-white hover:bg-accent-strong"
      >
        Try again
      </button>
    </main>
  );
}
