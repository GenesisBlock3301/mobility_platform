import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { DISCLAIMER } from "@/components/badges";
import { AlertIcon, ArrowLeftIcon, ArrowRightIcon } from "@/components/icons";
import { MatchCard } from "@/components/MatchCard";
import { api } from "@/lib/api";
import { FIELD_LABEL } from "@/lib/format";
import { handleMissingProfile, requireProfileId } from "@/lib/session";
import type { MatchFilter } from "@/lib/types";

export const metadata: Metadata = { title: "Your matches" };

// Filtering and paging happen in the API; these are only the chip labels.
const FILTERS: Record<MatchFilter, string> = {
  all: "All",
  strong: "Strong fit",
  verify: "Needs checking",
  clear: "No known blockers",
  blocked: "Blocked",
};
const PAGE_SIZE = 10;

type Props = { searchParams: Promise<{ filter?: string; page?: string }> };

function matchesHref(filter: MatchFilter, page = 1): string {
  const query = new URLSearchParams();
  if (filter !== "all") query.set("filter", filter);
  if (page > 1) query.set("page", String(page));
  const qs = query.toString();
  return qs ? `/matches?${qs}` : "/matches";
}

export default async function MatchesPage({ searchParams }: Props) {
  const id = await requireProfileId();
  const params = await searchParams;
  const filter: MatchFilter =
    params.filter && Object.hasOwn(FILTERS, params.filter) ? (params.filter as MatchFilter) : "all";
  const requested = Number.parseInt(params.page ?? "1", 10);
  const page = Number.isSafeInteger(requested) && requested >= 1 ? requested : 1;

  const [result, profile] = await Promise.all([
    api.listMatches(id, { page, pageSize: PAGE_SIZE, filter }),
    api.getProfile(id),
  ]).catch(handleMissingProfile);

  // A stale or hand-edited link past the last page goes to the last page instead of showing nothing.
  if (page > result.total_pages) redirect(matchesHref(filter, result.total_pages));

  const { counts } = result;
  const shownOpen = result.items.filter((m) => m.eligibility !== "blocked");
  const shownBlocked = result.items.filter((m) => m.eligibility === "blocked");
  const verifyCount = counts.verify;
  const missing = profile.completeness.missing;
  const firstShown = (result.page - 1) * result.page_size + 1;
  const lastShown = firstShown + result.items.length - 1;

  const tiles = [
    { value: counts.strong, label: "Strong fit, 75 or more", tone: "text-accent-strong" },
    { value: counts.partial, label: "Partial fit, 50 to 74", tone: "text-ink" },
    { value: counts.verify, label: "Need you to verify something", tone: "text-warn" },
    { value: counts.blocked, label: "Blocked by a requirement", tone: "text-stop" },
  ];

  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-6 px-4 pb-16 pt-10 sm:px-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-display text-4xl font-semibold tracking-tight">Your matches</h1>
        <p className="text-muted">
          {counts.all} roles scored against your profile, best fit first. Roles blocked by a hard requirement
          are listed separately at the bottom.
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {tiles.map((t) => (
          <div key={t.label} className="flex flex-col-reverse gap-0.5 rounded-xl border border-line bg-surface px-4 py-4">
            <dt className="text-sm text-muted">{t.label}</dt>
            <dd className={`font-mono text-[28px] font-medium ${t.tone}`}>{t.value}</dd>
          </div>
        ))}
      </dl>

      {missing.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 rounded-xl bg-warn-soft px-4 py-3.5 text-warn-strong">
          <AlertIcon className="size-5 text-warn" />
          <span className="min-w-0 flex-[1_1_420px] text-[15px]">
            {missing.includes("work_authorisations") && verifyCount > 0
              ? `Your profile does not say where you have the right to work, so ${verifyCount} roles are marked "verify". This does not lower their scores.`
              : `Your profile is ${profile.completeness.percent}% complete. Missing: ${missing
                  .map((f) => FIELD_LABEL[f].toLowerCase())
                  .join(", ")}. Scores are less reliable without them.`}
          </span>
          <Link href="/profile" className="font-semibold text-warn-strong underline">
            Update your profile
          </Link>
        </div>
      )}

      <nav aria-label="Filter matches" className="flex flex-wrap gap-2">
        {(Object.keys(FILTERS) as MatchFilter[]).map((key) => {
          const active = key === filter;
          return (
            <Link
              key={key}
              href={matchesHref(key)}
              aria-current={active ? "page" : undefined}
              className={`inline-flex min-h-11 items-center gap-1.5 rounded-full border px-4 text-[15px] font-semibold ${
                active ? "border-ink bg-ink text-white" : "border-field bg-surface text-ink hover:border-accent"
              }`}
            >
              {FILTERS[key]}
              <span className="font-mono font-normal">{counts[key]}</span>
            </Link>
          );
        })}
      </nav>

      {shownOpen.length > 0 && (
        <section aria-label="Open roles" className="flex flex-col gap-3.5">
          {shownOpen.map((m) => (
            <MatchCard key={m.opportunity.id} match={m} />
          ))}
        </section>
      )}

      {shownBlocked.length > 0 && (
        <section aria-labelledby="blocked-heading" className="flex flex-col gap-3.5 border-t border-line pt-6">
          <div className="flex flex-col gap-1">
            <h2 id="blocked-heading" className="font-display text-2xl font-semibold">
              Blocked by a requirement
            </h2>
            <p className="text-[15px] text-muted">
              These still suit you in other ways, so we show their real scores and exactly what stands in the way.
            </p>
          </div>
          {shownBlocked.map((m) => (
            <MatchCard key={m.opportunity.id} match={m} />
          ))}
        </section>
      )}

      {result.total_pages > 1 && (
        <nav aria-label="Pages" className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5">
          <p className="text-[15px] text-muted" aria-live="polite">
            Showing {firstShown}–{lastShown} of {result.total}
          </p>
          <div className="flex items-center gap-2">
            <PageLink href={matchesHref(filter, result.page - 1)} disabled={result.page <= 1} label="Previous">
              <ArrowLeftIcon className="size-[18px]" /> Previous
            </PageLink>
            <span className="px-2 font-mono text-[15px]">
              {result.page} / {result.total_pages}
            </span>
            <PageLink
              href={matchesHref(filter, result.page + 1)}
              disabled={result.page >= result.total_pages}
              label="Next"
            >
              Next <ArrowRightIcon className="size-[18px]" />
            </PageLink>
          </div>
        </nav>
      )}

      {result.items.length === 0 && (
        <p className="rounded-xl border border-dashed border-field bg-surface px-6 py-10 text-center text-muted">
          No roles match this filter.{" "}
          <Link href="/matches" className="font-semibold">
            Show all roles
          </Link>
        </p>
      )}

      <p className="text-[13px] text-muted">{DISCLAIMER}</p>
    </main>
  );
}

function PageLink({
  href,
  disabled,
  label,
  children,
}: {
  href: string;
  disabled: boolean;
  label: string;
  children: React.ReactNode;
}) {
  const base = "inline-flex min-h-11 items-center gap-1.5 rounded-full border px-4 text-[15px] font-semibold";
  if (disabled) {
    return (
      <span aria-disabled="true" aria-label={`${label} page`} className={`${base} border-line text-muted opacity-60`}>
        {children}
      </span>
    );
  }
  return (
    <Link href={href} aria-label={`${label} page`} className={`${base} border-field bg-surface text-ink hover:border-accent`}>
      {children}
    </Link>
  );
}
