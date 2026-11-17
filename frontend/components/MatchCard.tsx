import Link from "next/link";
import { placeLine } from "@/lib/format";
import type { MatchSummary } from "@/lib/types";
import { BandBadge, EligibilityBadge, ScoreRing } from "./badges";
import { BlockIcon, CheckIcon, DashIcon } from "./icons";
import { ShortlistButton } from "./ShortlistButton";

export function MatchCard({ match }: { match: MatchSummary }) {
  const o = match.opportunity;
  return (
    <article className="flex flex-wrap items-center gap-x-7 gap-y-5 rounded-[14px] border border-line bg-surface px-6 py-5">
      <span className="w-8 shrink-0 font-mono text-[15px] text-muted">#{match.rank}</span>
      <div className="flex min-w-0 flex-[1_1_280px] flex-col gap-1.5">
        <span className="font-mono text-[13px] text-muted">{placeLine(o)}</span>
        <h2 className="font-display text-[21px] font-semibold leading-tight">
          <Link href={`/matches/${o.id}`} className="text-ink hover:text-accent">
            {o.title}
          </Link>
        </h2>
        <span className="text-[15px] text-muted">{o.organisation}</span>
        <div className="flex flex-wrap gap-2 pt-1">
          <BandBadge band={match.band} />
          <EligibilityBadge match={match} />
        </div>
      </div>
      <ul className="flex min-w-0 flex-[1_1_300px] flex-col gap-1.5 text-sm">
        {match.headline_strengths.slice(0, 1).map((s) => (
          <li key={s} className="flex gap-2">
            <CheckIcon className="mt-0.5 size-4 text-ok" />
            {s}
          </li>
        ))}
        {match.headline_gaps.slice(0, 1).map((g) => (
          <li key={g} className="flex gap-2 text-muted">
            <DashIcon className="mt-0.5 size-4 text-warn" />
            {g}
          </li>
        ))}
        {match.eligibility === "blocked" && match.eligibility_summary && (
          <li className="flex gap-2 font-medium text-stop">
            <BlockIcon className="mt-0.5 size-4" />
            {match.eligibility_summary}
          </li>
        )}
      </ul>
      <div className="flex shrink-0 items-center gap-4">
        <ScoreRing score={match.score} band={match.band} />
        <div className="flex flex-col gap-2">
          <Link
            href={`/matches/${o.id}`}
            className="inline-flex min-h-10 items-center justify-center rounded-lg bg-accent px-3.5 text-sm font-semibold text-white hover:bg-accent-strong"
          >
            {match.eligibility === "blocked" ? "See what would change" : "View details"}
            <span className="sr-only"> for {o.title}</span>
          </Link>
          <ShortlistButton opportunityId={o.id} title={o.title} saved={match.shortlisted} />
        </div>
      </div>
    </article>
  );
}
