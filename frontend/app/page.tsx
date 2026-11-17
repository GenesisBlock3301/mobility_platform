import Link from "next/link";
import { AlertIcon, ArrowRightIcon, CheckIcon, ShieldIcon } from "@/components/icons";
import { getProfileId } from "@/lib/session";

const STEPS = [
  {
    title: "Describe yourself",
    text: "Education, experience, skills, languages and where you would like to work. Skip anything you are unsure of.",
  },
  {
    title: "Get a ranked list",
    text: "Each role is scored out of 100 on six criteria: skills, experience, education, language, location and interests.",
  },
  {
    title: "Know what to check",
    text: "Visa, enrolment and language requirements are listed separately, with a checklist of what to confirm.",
  },
];

export default async function HomePage() {
  const hasProfile = Boolean(await getProfileId());
  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-16 px-4 pb-16 pt-16 sm:px-8">
      <section className="flex flex-wrap items-center gap-14">
        <div className="flex min-w-0 flex-[1_1_460px] flex-col gap-6">
          <span className="font-mono text-[13px] uppercase tracking-[0.08em] text-accent">
            International career mobility
          </span>
          <h1 className="text-balance font-display text-[44px] font-semibold leading-[1.08] tracking-tight sm:text-[52px]">
            See which roles abroad fit you, and what stands in the way.
          </h1>
          <p className="max-w-[34em] text-[19px] text-muted">
            Tell us about your studies, skills and languages. We score opportunities across countries, explain every
            score, and flag anything you need to check before applying.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            {hasProfile ? (
              <>
                <Link
                  href="/matches"
                  className="inline-flex min-h-12 items-center gap-2.5 rounded-[10px] bg-accent px-6 text-[17px] font-semibold text-white hover:bg-accent-strong"
                >
                  See my matches <ArrowRightIcon className="size-[18px]" />
                </Link>
                <Link
                  href="/profile"
                  className="inline-flex min-h-12 items-center rounded-[10px] border border-field bg-surface px-6 text-[17px] font-semibold text-ink"
                >
                  Edit my profile
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/profile"
                  className="inline-flex min-h-12 items-center gap-2.5 rounded-[10px] bg-accent px-6 text-[17px] font-semibold text-white hover:bg-accent-strong"
                >
                  Build my profile <ArrowRightIcon className="size-[18px]" />
                </Link>
                <Link
                  href="/profile?sample=1"
                  className="inline-flex min-h-12 items-center rounded-[10px] border border-field bg-surface px-6 text-[17px] font-semibold text-ink"
                >
                  Try the sample profile
                </Link>
              </>
            )}
          </div>
          <p className="text-sm text-muted">Takes about 3 minutes. No name or email needed.</p>
        </div>

        <div className="flex min-w-0 flex-[1_1_400px] flex-col gap-3.5">
          <div className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-6 shadow-[0_12px_32px_rgba(20,32,43,0.08)]">
            <div className="flex items-start justify-between gap-4">
              <div className="flex min-w-0 flex-col gap-1">
                <span className="font-mono text-[13px] text-muted">DE · BERLIN · HYBRID</span>
                <span className="font-display text-[22px] font-semibold">Programme Assistant</span>
                <span className="text-muted">International NGO</span>
              </div>
              <div
                className="flex size-[76px] shrink-0 items-center justify-center rounded-full"
                style={{ background: "conic-gradient(var(--color-accent) 327.6deg, var(--color-track) 0)" }}
                role="img"
                aria-label="Example fit score 91 out of 100"
              >
                <div className="flex size-[60px] flex-col items-center justify-center rounded-full bg-surface">
                  <span className="font-mono text-xl font-medium leading-none">91</span>
                  <span className="text-[11px] text-muted">of 100</span>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-[13px] font-semibold text-accent-strong">
                Strong fit
              </span>
              <span className="rounded-full bg-warn-soft px-2.5 py-0.5 text-[13px] font-semibold text-warn">
                Verify 2 items
              </span>
            </div>
            <ul className="flex flex-col gap-2 text-[15px]">
              <li className="flex gap-2">
                <CheckIcon className="mt-1 size-4 text-ok" />3 of 3 required skills, including reporting
              </li>
              <li className="flex gap-2">
                <CheckIcon className="mt-1 size-4 text-ok" />
                Germany is one of your preferred countries
              </li>
              <li className="flex gap-2">
                <AlertIcon className="mt-1 size-4 text-warn" />
                Check your right to work in Germany
              </li>
            </ul>
          </div>
          <span className="text-center text-[13px] text-muted">
            An example result for the sample profile. Every score shows where its points came from.
          </span>
        </div>
      </section>

      <section className="flex flex-col gap-6">
        <h2 className="font-display text-[28px] font-semibold">How it works</h2>
        <ol className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <li key={step.title} className="flex flex-col gap-2.5 rounded-[14px] border border-line bg-surface p-6">
              <span className="font-mono text-sm text-accent">Step {i + 1}</span>
              <h3 className="text-[19px] font-semibold">{step.title}</h3>
              <p className="text-muted">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex flex-wrap items-center gap-x-10 gap-y-3 rounded-[14px] bg-accent-soft px-6 py-5 text-accent-strong">
        <span className="flex items-center gap-2.5 font-semibold">
          <ShieldIcon className="size-5" /> We never guess your visa status
        </span>
        <span className="min-w-0 flex-[1_1_420px] text-[15px]">
          If you do not tell us whether you can work in a country, roles there are marked &ldquo;verify&rdquo;, never
          &ldquo;eligible&rdquo;. Our notes are guidance, not legal advice.
        </span>
      </section>
    </main>
  );
}
