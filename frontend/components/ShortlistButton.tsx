"use client";

import { useOptimistic, useState, useTransition } from "react";
import { toggleShortlist } from "@/app/actions";
import { BookmarkIcon } from "./icons";

type Props = {
  opportunityId: string;
  title: string;
  saved: boolean;
  variant?: "compact" | "large" | "remove";
};

export function ShortlistButton({ opportunityId, title, saved, variant = "compact" }: Props) {
  const [optimisticSaved, setOptimisticSaved] = useOptimistic(saved);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onClick() {
    const next = !optimisticSaved;
    setError(null);
    startTransition(async () => {
      setOptimisticSaved(next);
      const result = await toggleShortlist(opportunityId, next);
      // On failure the optimistic value is dropped when the transition ends,
      // so the button rolls back to the server's state.
      if (!result.ok) setError(result.message);
    });
  }

  if (variant === "remove") {
    return (
      <span className="inline-flex flex-col">
        <button
          type="button"
          onClick={onClick}
          disabled={pending}
          className="min-h-10 rounded-lg px-3.5 text-sm font-semibold text-stop hover:bg-stop-soft disabled:opacity-60"
        >
          Remove<span className="sr-only"> {title} from your shortlist</span>
        </button>
        <span aria-live="polite" className="text-xs text-stop">{error}</span>
      </span>
    );
  }

  const large = variant === "large";
  const on = optimisticSaved;
  const tone = on
    ? "border-accent bg-accent-soft text-accent-strong"
    : large
      ? "border-accent bg-accent text-white hover:bg-accent-strong"
      : "border-field bg-surface text-ink hover:border-accent";
  const label = on ? (large ? "Saved to shortlist" : "Saved") : large ? "Save to shortlist" : "Save";

  return (
    <span className="inline-flex flex-col items-stretch gap-1">
      <button
        type="button"
        aria-pressed={on}
        onClick={onClick}
        disabled={pending}
        className={`inline-flex items-center justify-center gap-2 rounded-lg border font-semibold transition-colors disabled:cursor-wait ${
          large ? "min-h-12 px-5" : "min-h-10 px-3.5 text-sm"
        } ${tone}`}
      >
        <BookmarkIcon filled={on} className={large ? "size-[17px]" : "size-[15px]"} />
        {label}
        <span className="sr-only"> {title}</span>
      </button>
      <span aria-live="polite" className="max-w-48 text-xs text-stop">
        {error}
      </span>
    </span>
  );
}
