// Zod schema mirroring the API's ProfileIn model. The API validates again; this
// gives the user field errors without a round trip.

import { z } from "zod";

export const LANGUAGE_LEVELS = ["basic", "conversational", "professional", "fluent", "native"] as const;
export const EDUCATION_LEVELS = ["secondary", "diploma", "bachelor", "master", "doctorate"] as const;

const shortText = z
  .string()
  .trim()
  .min(1, "This can't be empty.")
  .max(60, "Use 60 characters or fewer.");

// Required: education level, years of experience, at least one skill and one language
// (the API enforces the same four). Everything else may be left empty.
export const profileSchema = z.strictObject({
  education_level: z
    .enum(EDUCATION_LEVELS)
    .nullable()
    .refine((v): boolean => v !== null, "Choose your highest education."),
  field_of_study: z.string().trim().max(120, "Use 120 characters or fewer.").nullable(),
  years_experience: z
    .number("Enter a number of years.")
    .min(0, "Years of experience can't be negative.")
    .max(60, "Enter 60 years or fewer.")
    .refine((v) => Math.abs(v * 10 - Math.round(v * 10)) < 1e-9, "Use at most one decimal place, for example 2.5.")
    .nullable()
    .refine((v): boolean => v !== null, "Enter your years of work experience."),
  experience_summary: z.string().trim().max(500, "Use 500 characters or fewer.").nullable(),
  skills: z.array(shortText).min(1, "Add at least one skill.").max(50, "Add 50 skills or fewer."),
  languages: z
    .array(
      z.strictObject({
        language: z.string().trim().min(1, "Enter a language name.").max(40, "Use 40 characters or fewer."),
        level: z.enum(LANGUAGE_LEVELS),
      }),
    )
    .min(1, "Add at least one language.")
    .max(15, "Add 15 languages or fewer.")
    .refine(
      (langs) => new Set(langs.map((l) => l.language.trim().toLowerCase())).size === langs.length,
      "Each language can be listed only once.",
    ),
  preferred_countries: z.array(z.string().length(2)).max(20, "Choose 20 countries or fewer."),
  career_interests: z.array(shortText).max(20, "Add 20 interests or fewer."),
  work_authorisations: z.array(
    z.strictObject({
      country_code: z.string().length(2),
      status: z.enum(["authorised", "not_authorised"]),
    }),
  ),
  is_current_student: z.boolean().nullable(),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;

export type FieldErrors = Record<string, string>;

export function issuesToErrors(issues: z.core.$ZodIssue[]): FieldErrors {
  const errors: FieldErrors = {};
  for (const issue of issues) {
    const key = issue.path.join(".") || "form";
    errors[key] ??= issue.message;
  }
  return errors;
}

export const opportunityIdSchema = z.uuid();
