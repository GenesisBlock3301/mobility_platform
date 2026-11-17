import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BandBadge, DISCLAIMER, EligibilityBadge, ScoreRing } from "@/components/badges";
import { AlertIcon, ArrowLeftIcon, BlockIcon, CheckIcon, DashIcon } from "@/components/icons";
import { ShortlistButton } from "@/components/ShortlistButton";
import { VerificationChecklist } from "@/components/VerificationChecklist";
import { api, isNotFound } from "@/lib/api";
import { countryName, CRITERION_LABEL, EDUCATION_LABEL, placeLine, points, years } from "@/lib/format";
import { opportunityIdSchema } from "@/lib/schemas";
import { handleMissingProfile, requireProfileId } from "@/lib/session";
import type { EligibilityCheck, MatchDetail } from "@/lib/types";

export const metadata: Metadata = { title: "Role details" };

type Props = { params: Promise<{ id: string }> };

async function load(profileId: string, opportunityId: string): Promise<MatchDetail> {
  try {
    return await api.getMatch(profileId, opportunityId);
  } catch (error) {
    // The API says which resource is missing: a deleted profile resets the session,
    // an unknown role shows the not-found page.
    if (isNotFound(error, "opportunity")) notFound();
    return handleMissingProfile(error);
  }
}

const CHECK_STYLE: Record<EligibilityCheck["status"], { box: string; icon: React.ReactNode; label: string }> = {
  met: { box: "bg-ok-soft text-ok-strong", icon: <CheckIcon className="mt-0.5 size-[18px] text-ok" />, label: "Met" },
  verification_required: {
    box: "bg-warn-soft text-warn-strong",
    icon: <AlertIcon className="mt-0.5 size-[18px] text-warn" />,
    label: "Verify",
  },
  not_met: { box: "bg-stop-soft text-stop-strong", icon: <BlockIcon className="mt-0.5 size-[18px] text-stop" />, label: "Not met" },
};

const KIND_LABEL: Record<EligibilityCheck["kind"], string> = {
  language: "Language",
  work_authorisation: "Right to work",
  enrolment: "Student enrolment",
};

const SPONSORSHIP: Record<string, string> = {
  available: "Visa sponsorship offered",
  not_available: "No visa sponsorship",
  unknown: "Sponsorship policy not stated",
};

export default async function MatchDetailPage({ params }: Props) {
  const { id: opportunityId } = await params;
  if (!opportunityIdSchema.safeParse(opportunityId).success) notFound();
  const profileId = await requireProfileId();
  const match = await load(profileId, opportunityId);
  const o = match.opportunity;
  const blocked = match.eligibility === "blocked";
  const blockers = match.eligibility_checks.filter((c) => c.status === "not_met");

  const requirements: [string, string][] = [
    ["Education", o.min_education_level ? `${EDUCATION_LABEL[o.min_education_level]} or above` : "No level stated"],
    ["Fields accepted", o.education_fields.join(", ") || "Any"],
    ["Experience", years(o)],
    ["Required skills", o.required_skills.join(", ") || "None stated"],
    ["Preferred skills", o.preferred_skills.join(", ") || "None stated"],
    ["Languages", o.language_requirements.map((l) => `${l.language} (${l.level})`).join(", ") || "None stated"],
    [
      "Eligibility",
      [
        o.requires_local_work_authorisation ? `Right to work in ${countryName(o.country_code)}` : "No local work permit needed",
        o.requires_local_work_authorisation ? SPONSORSHIP[o.visa_sponsorship] : null,
        o.requires_current_student ? "Must be a currently enrolled student" : null,
      ]
        .filter(Boolean)
        .join(". "),
    ],
  ];

  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-6 px-4 pb-16 pt-7 sm:px-8">
      <Link href="/matches" className="inline-flex min-h-11 items-center gap-1.5 self-start font-semibold">
        <ArrowLeftIcon /> Back to matches
      </Link>

      <section className="flex flex-wrap items-center gap-x-10 gap-y-6 rounded-2xl border border-line bg-surface p-5 sm:p-7">
        <div className="flex min-w-0 flex-[1_1_460px] flex-col gap-2">
          <span className="font-mono text-[13px] text-muted">
            #{match.rank} · {placeLine(o)} · {o.opportunity_type.toUpperCase()}
          </span>
          <h1 className="text-balance font-display text-[30px] font-semibold leading-tight tracking-tight sm:text-[38px]">
            {o.title}
          </h1>
          <span className="text-lg text-muted">{o.organisation}</span>
          <p className="max-w-[65ch] text-[15px] text-muted">{o.description}</p>
          <div className="flex flex-wrap gap-2 pt-1.5">
            <BandBadge band={match.band} />
            <EligibilityBadge match={match} />
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap items-center gap-4 sm:gap-6">
          <ScoreRing score={match.score} band={match.band} size="lg" />
          <ShortlistButton opportunityId={o.id} title={o.title} saved={match.shortlisted} variant="large" />
        </div>
      </section>

      {blocked && blockers.length > 0 && (
        <section className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-[14px] bg-stop-soft px-6 py-5 text-stop-strong">
          <BlockIcon className="size-7 text-stop" />
          <div className="flex min-w-0 flex-[1_1_420px] flex-col gap-0.5">
            <b className="text-lg">Blocked by a hard requirement</b>
            {blockers.map((b) => (
              <span key={b.message} className="text-[15px]">
                {b.message}
              </span>
            ))}
            <span className="text-[15px]">The score below is still calculated, so you can see how close this role is.</span>
          </div>
        </section>
      )}

      <div className="flex flex-wrap items-start gap-6">
        <div className="flex min-w-0 flex-[999_1_560px] flex-col gap-6">
          <section className="flex flex-col gap-3 rounded-[14px] border border-line bg-surface p-6">
            <h2 className="font-display text-[22px] font-semibold">Why this score</h2>
            <p className="text-[17px] leading-relaxed">{match.explanation}</p>
          </section>

          <section className="flex flex-col gap-4 rounded-[14px] border border-line bg-surface p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="font-display text-[22px] font-semibold">Score breakdown</h2>
              <span className="font-mono text-sm text-muted">{match.score} / 100</span>
            </div>
            <ul className="flex flex-col">
              {match.criteria.map((c) => {
                const pct = Math.round((c.points_earned / c.points_possible) * 100);
                const color = pct === 100 ? "var(--color-accent)" : pct === 0 ? "var(--color-stop)" : "var(--color-accent-mid)";
                return (
                  <li
                    key={c.criterion}
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1.5 border-t border-neutral-soft py-3 sm:grid-cols-[minmax(110px,150px)_minmax(0,1fr)_64px] sm:py-2.5"
                  >
                    <span className="font-semibold">{CRITERION_LABEL[c.criterion] ?? c.criterion}</span>
                    <div
                      className="order-3 col-span-2 h-3 overflow-hidden rounded-full bg-track sm:order-none sm:col-span-1"
                      role="img"
                      aria-label={`${points(c.points_earned)} of ${c.points_possible} points`}
                    >
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
                    </div>
                    <span className="order-2 text-right font-mono text-sm sm:order-none">
                      {points(c.points_earned)}/{c.points_possible}
                    </span>
                    <span className="order-4 col-span-2 text-sm text-muted sm:order-none sm:col-span-1 sm:col-start-2 sm:col-end-4">
                      {c.note}
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="flex flex-col gap-3.5 rounded-[14px] border border-line bg-surface p-6">
            <h2 className="font-display text-[22px] font-semibold">What the role asks for</h2>
            <dl className="grid grid-cols-1 gap-x-5 gap-y-3 text-[15px] sm:grid-cols-[minmax(140px,200px)_minmax(0,1fr)]">
              {requirements.map(([label, value]) => (
                <div key={label} className="flex flex-col gap-0.5 sm:contents">
                  <dt className="text-muted">{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>

        <aside className="flex min-w-0 flex-[1_1_340px] flex-col gap-5">
          <section className="flex flex-col gap-3.5 rounded-[14px] border border-line bg-surface p-5">
            <h2 className="font-display text-xl font-semibold">Eligibility</h2>
            <p className="text-sm text-muted">Checked separately from the score.</p>
            {match.eligibility_checks.length === 0 && (
              <p className="flex gap-2 text-sm">
                <DashIcon className="mt-0.5 size-4 text-muted" /> No eligibility requirements stated.
              </p>
            )}
            <ul className="flex flex-col gap-2.5">
              {match.eligibility_checks.map((c) => {
                const style = CHECK_STYLE[c.status];
                return (
                  <li key={`${c.kind}-${c.message}`} className={`flex items-start gap-3 rounded-[10px] p-3 ${style.box}`}>
                    {style.icon}
                    <div className="flex flex-col gap-0.5 text-sm">
                      <b>
                        {KIND_LABEL[c.kind]}: {style.label.toLowerCase()}
                      </b>
                      <span>{c.message}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          {match.verification_checklist.length > 0 && (
            <section className="rounded-[14px] border border-line bg-surface p-5">
              <VerificationChecklist opportunityId={o.id} items={match.verification_checklist} />
            </section>
          )}

          {match.what_if.length > 0 && (
            <section className={`flex flex-col gap-3 rounded-[14px] bg-surface p-5 ${blocked ? "border-2 border-accent" : "border border-line"}`}>
              <h2 className="font-display text-xl font-semibold">What would change this</h2>
              <ul className="flex flex-col gap-2">
                {match.what_if.map((w) => (
                  <li key={w.change} className="flex flex-col gap-1 rounded-[10px] border border-dashed border-field px-3.5 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[15px]">{w.change}</span>
                      <span className="whitespace-nowrap font-mono text-[15px] text-accent-strong">
                        {match.score} → {w.new_score}
                      </span>
                    </div>
                    {w.unblocks && (
                      <span className="flex gap-1.5 text-sm text-ok">
                        <CheckIcon className="mt-0.5 size-4" /> No longer blocked
                        {w.new_eligibility === "requires_verification" ? ", though you would still need to verify other items" : ""}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
              <Link href="/profile" className="text-[15px] font-semibold">
                Update my profile
              </Link>
            </section>
          )}

          <p className="text-[13px] text-muted">{DISCLAIMER}</p>
        </aside>
      </div>
    </main>
  );
}
