import type { Metadata } from "next";
import Link from "next/link";
import { EligibilityBadge } from "@/components/badges";
import { BookmarkIcon } from "@/components/icons";
import { ShortlistButton } from "@/components/ShortlistButton";
import { VerificationChecklist } from "@/components/VerificationChecklist";
import { api } from "@/lib/api";
import { placeLine } from "@/lib/format";
import { handleMissingProfile, requireProfileId } from "@/lib/session";

export const metadata: Metadata = { title: "Your shortlist" };

export default async function ShortlistPage() {
  const id = await requireProfileId();
  const items = await api.listShortlist(id).catch(handleMissingProfile);

  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-6 px-4 pb-16 pt-10 sm:px-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-display text-4xl font-semibold tracking-tight">Your shortlist</h1>
        <p className="text-muted">Roles you saved, with what is left to check before you apply.</p>
      </div>

      {items.length === 0 ? (
        <section className="flex flex-col items-center gap-3 rounded-[14px] border border-dashed border-field bg-surface px-6 py-12 text-center">
          <BookmarkIcon className="size-9 text-faint" />
          <h2 className="font-display text-[22px] font-semibold">Nothing saved yet</h2>
          <p className="max-w-[36em] text-muted">
            Save a role from your matches and it appears here with a checklist of what to confirm.
          </p>
          <Link
            href="/matches"
            className="inline-flex min-h-11 items-center rounded-[10px] bg-accent px-5 font-semibold text-white hover:bg-accent-strong"
          >
            Browse my matches
          </Link>
        </section>
      ) : (
        <ul className="flex flex-col gap-4">
          {items.map((m) => {
            const o = m.opportunity;
            return (
              <li
                key={o.id}
                className="flex flex-wrap gap-x-8 gap-y-5 rounded-[14px] border border-line bg-surface px-6 py-5"
              >
                <div className="flex min-w-0 flex-[1_1_340px] flex-col gap-1.5">
                  <span className="font-mono text-[13px] text-muted">{placeLine(o)}</span>
                  <h2 className="font-display text-[21px] font-semibold">{o.title}</h2>
                  <span className="text-[15px] text-muted">{o.organisation}</span>
                  <div className="flex flex-wrap items-center gap-2.5 pt-1.5">
                    <span className="font-mono text-[15px] text-accent-strong">fit {m.score}/100</span>
                    <EligibilityBadge match={m} />
                  </div>
                  <div className="flex flex-wrap items-start gap-2 pt-2">
                    <Link
                      href={`/matches/${o.id}`}
                      className="inline-flex min-h-10 items-center rounded-lg border border-field px-3.5 text-sm font-semibold text-ink hover:border-accent"
                    >
                      View details
                    </Link>
                    <ShortlistButton opportunityId={o.id} title={o.title} saved variant="remove" />
                  </div>
                </div>
                <div className="min-w-0 flex-[1_1_380px]">
                  <VerificationChecklist opportunityId={o.id} items={m.verification_checklist} showStatus />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
