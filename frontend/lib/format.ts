import type { Band, EducationLevel, Eligibility, MatchSummary, Opportunity } from "./types";

const regionNames = new Intl.DisplayNames(["en"], { type: "region" });

export function countryName(code: string): string {
  try {
    return regionNames.of(code.toUpperCase()) ?? code;
  } catch {
    return code;
  }
}

const WORK_MODE: Record<Opportunity["work_mode"], string> = {
  onsite: "On-site",
  hybrid: "Hybrid",
  remote: "Remote",
};

export function placeLine(o: Opportunity): string {
  return [o.country_code, o.city, WORK_MODE[o.work_mode]].join(" · ").toUpperCase();
}

export const EDUCATION_LABEL: Record<EducationLevel, string> = {
  secondary: "Secondary school",
  diploma: "Diploma",
  bachelor: "Bachelor's degree",
  master: "Master's degree",
  doctorate: "Doctorate",
};

export const BAND_LABEL: Record<Band, string> = {
  strong: "Strong fit",
  partial: "Partial fit",
  poor: "Poor fit",
};

export const ELIGIBILITY_LABEL: Record<Eligibility, string> = {
  no_known_blockers: "No known blockers",
  requires_verification: "Verify before applying",
  blocked: "Blocked",
};

export function eligibilityLabel(m: MatchSummary): string {
  if (m.eligibility !== "requires_verification") return ELIGIBILITY_LABEL[m.eligibility];
  const count = m.verification_checklist.length;
  return count > 0 ? `Verify ${count} ${count === 1 ? "item" : "items"}` : "Verify before applying";
}

export const CRITERION_LABEL: Record<string, string> = {
  skills: "Skills",
  experience: "Experience",
  education: "Education",
  language: "Language",
  location: "Location",
  interests: "Interests",
};

export function points(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function years(o: Opportunity): string {
  const lo = o.min_years_experience;
  const hi = o.max_years_experience;
  if (lo != null && hi != null) return `${lo} to ${hi} years`;
  if (lo != null) return `At least ${lo} ${lo === 1 ? "year" : "years"}`;
  if (hi != null) return `Up to ${hi} years`;
  return "Not stated";
}

export const FIELD_LABEL: Record<string, string> = {
  education_level: "Education level",
  field_of_study: "Field of study",
  years_experience: "Years of experience",
  skills: "Skills",
  languages: "Languages",
  preferred_countries: "Preferred countries",
  career_interests: "Career interests",
  work_authorisations: "Right to work",
  is_current_student: "Student status",
};
