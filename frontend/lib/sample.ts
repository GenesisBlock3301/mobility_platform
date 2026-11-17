import type { ProfileInput } from "./types";

// The fictional sample candidate from the assessment brief.
export const SAMPLE_PROFILE: ProfileInput = {
  education_level: "bachelor",
  field_of_study: "Business Administration",
  years_experience: 2,
  experience_summary: "Business operations and project support",
  skills: ["Excel", "Research", "Stakeholder communication", "Reporting", "Project coordination"],
  languages: [
    { language: "Bengali", level: "native" },
    { language: "English", level: "professional" },
  ],
  preferred_countries: ["DE", "CA", "SG"],
  career_interests: ["Programme support", "Business operations", "Project coordination"],
  work_authorisations: [],
  is_current_student: null,
};

export const EMPTY_PROFILE: ProfileInput = {
  education_level: null,
  field_of_study: null,
  years_experience: null,
  experience_summary: null,
  skills: [],
  languages: [],
  preferred_countries: [],
  career_interests: [],
  work_authorisations: [],
  is_current_student: null,
};
