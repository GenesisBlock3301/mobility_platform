import { BAND_LABEL, eligibilityLabel } from "@/lib/format";
import type { Band, MatchSummary } from "@/lib/types";

const chip = "inline-flex items-center rounded-full px-2.5 py-0.5 text-[13px] font-semibold whitespace-nowrap";

export function BandBadge({ band }: { band: Band }) {
  const tone = band === "strong" ? "bg-accent-soft text-accent-strong" : "bg-neutral-soft text-neutral-strong";
  return <span className={`${chip} ${tone}`}>{BAND_LABEL[band]}</span>;
}

export function EligibilityBadge({ match }: { match: MatchSummary }) {
  const tone = {
    no_known_blockers: "bg-ok-soft text-ok",
    requires_verification: "bg-warn-soft text-warn",
    blocked: "bg-stop-soft text-stop",
  }[match.eligibility];
  return <span className={`${chip} ${tone}`}>{eligibilityLabel(match)}</span>;
}

export function ScoreRing({ score, band, size = "md" }: { score: number; band: Band; size?: "md" | "lg" }) {
  const color = band === "strong" ? "var(--color-accent)" : band === "partial" ? "var(--color-accent-mid)" : "var(--color-faint)";
  const outer = size === "lg" ? "size-28" : "size-16";
  const inner = size === "lg" ? "size-[90px]" : "size-[50px]";
  return (
    <div
      role="img"
      aria-label={`Fit score ${score} out of 100`}
      className={`${outer} flex shrink-0 items-center justify-center rounded-full`}
      style={{ background: `conic-gradient(${color} ${score * 3.6}deg, var(--color-track) 0)` }}
    >
      <div className={`${inner} flex flex-col items-center justify-center rounded-full bg-surface`}>
        <span className={`font-mono font-medium leading-none ${size === "lg" ? "text-[32px]" : "text-lg"}`}>
          {score}
        </span>
        {size === "lg" && <span className="text-xs text-muted">of 100</span>}
      </div>
    </div>
  );
}

export const DISCLAIMER =
  "Eligibility notes are based only on what you entered. They are not legal advice or a confirmed immigration status.";
