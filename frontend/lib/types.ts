// Shapes returned by the FastAPI service. Kept in step with backend/app/schemas/models.py.

import type { EDUCATION_LEVELS, LANGUAGE_LEVELS, ProfileFormValues } from "./schemas";

export type LanguageLevel = (typeof LANGUAGE_LEVELS)[number];
export type EducationLevel = (typeof EDUCATION_LEVELS)[number];
export type Band = "strong" | "partial" | "poor";
export type Eligibility = "no_known_blockers" | "requires_verification" | "blocked";

export interface LanguageSkill {
  language: string;
  level: LanguageLevel;
}

export interface WorkAuthorisation {
  country_code: string;
  status: "authorised" | "not_authorised";
}

/** What the profile form sends: exactly the Zod schema's output. */
export type ProfileInput = ProfileFormValues;

export interface Profile extends Omit<ProfileInput, "years_experience"> {
  id: string;
  years_experience: string | number | null;
  completeness: { percent: number; missing: string[] };
  updated_at: string;
}

export interface Opportunity {
  id: string;
  slug: string;
  title: string;
  organisation: string;
  opportunity_type: "job" | "internship";
  country_code: string;
  city: string;
  work_mode: "onsite" | "hybrid" | "remote";
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience: number | null;
  max_years_experience: number | null;
  min_education_level: EducationLevel | null;
  education_fields: string[];
  language_requirements: LanguageSkill[];
  requires_local_work_authorisation: boolean;
  visa_sponsorship: "available" | "not_available" | "unknown";
  requires_current_student: boolean;
  interest_tags: string[];
}

export interface MatchSummary {
  rank: number;
  opportunity: Opportunity;
  score: number;
  band: Band;
  eligibility: Eligibility;
  headline_strengths: string[];
  headline_gaps: string[];
  eligibility_summary: string | null;
  verification_checklist: string[];
  shortlisted: boolean;
}

export type MatchFilter = "all" | "strong" | "verify" | "clear" | "blocked";

/** Counts over the whole ranking, unaffected by the filter or the page. */
export interface MatchCounts {
  all: number;
  strong: number;
  partial: number;
  verify: number;
  clear: number;
  blocked: number;
}

export interface MatchPage {
  items: MatchSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  filter: MatchFilter;
  counts: MatchCounts;
}

export interface Criterion {
  criterion: string;
  points_earned: number;
  points_possible: number;
  status: "met" | "partly_met" | "not_met" | "no_requirement" | "unknown";
  note: string;
  matched: string[];
  missing: string[];
}

export interface EligibilityCheck {
  kind: "language" | "work_authorisation" | "enrolment";
  status: "met" | "not_met" | "verification_required";
  message: string;
}

export interface WhatIf {
  change: string;
  new_score: number;
  gain: number;
  new_eligibility: Eligibility;
  unblocks: boolean;
}

export interface MatchDetail extends MatchSummary {
  criteria: Criterion[];
  eligibility_checks: EligibilityCheck[];
  explanation: string;
  what_if: WhatIf[];
}

export interface Problem {
  title: string;
  status: number;
  detail: string;
  errors?: { field: string; message: string }[];
  /** On a 404: which resource is missing. */
  resource?: "profile" | "opportunity";
  request_id?: string;
}
