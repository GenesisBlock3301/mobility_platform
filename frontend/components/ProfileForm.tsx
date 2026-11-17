"use client";

import { useActionState, useEffect, useMemo, useRef, useState } from "react";
import { useFormStatus } from "react-dom";
import { type ProfileFormState, saveProfile } from "@/app/actions";
import { COUNTRY_CODES } from "@/lib/countries";
import { countryName, EDUCATION_LABEL, FIELD_LABEL } from "@/lib/format";
import { SAMPLE_PROFILE } from "@/lib/sample";
import { EDUCATION_LEVELS, type FieldErrors, issuesToErrors, LANGUAGE_LEVELS, profileSchema } from "@/lib/schemas";
import type { EducationLevel, LanguageLevel, ProfileInput } from "@/lib/types";
import { FieldMarker } from "./FieldMarker";
import { AlertIcon, ArrowRightIcon, CheckIcon } from "./icons";
import { TagInput } from "./TagInput";

type WorkChoice = "unknown" | "authorised" | "not_authorised";
type StudentChoice = "unknown" | "yes" | "no";

type Draft = {
  education_level: string;
  field_of_study: string;
  years_experience: string;
  experience_summary: string;
  skills: string[];
  languages: { language: string; level: LanguageLevel }[];
  preferred_countries: string[];
  career_interests: string[];
  work: Record<string, WorkChoice>;
  student: StudentChoice;
};

type SectionId = "education" | "skills" | "places" | "eligibility";

// Each tab owns these top-level field keys, which are also the keys used in FieldErrors
// ("languages.0.language" belongs to "languages"). "form" errors are shown under languages.
const SECTIONS: { id: SectionId; label: string; fields: string[] }[] = [
  {
    id: "education",
    label: "Education",
    fields: ["education_level", "field_of_study", "years_experience", "experience_summary"],
  },
  { id: "skills", label: "Skills & languages", fields: ["skills", "languages", "form"] },
  { id: "places", label: "Where & what", fields: ["preferred_countries", "career_interests"] },
  { id: "eligibility", label: "Eligibility", fields: ["work_authorisations", "is_current_student"] },
];

function sectionOf(key: string): SectionId {
  const root = key.split(".")[0];
  return SECTIONS.find((s) => s.fields.includes(root))?.id ?? "education";
}

// The element to focus when the summary links to a field that is not stated.
const FIELD_FOCUS_ID: Record<string, string> = { languages: "languages-add" };

const WORK_OPTIONS: { value: WorkChoice; label: string }[] = [
  { value: "unknown", label: "Not stated" },
  { value: "authorised", label: "I can work here" },
  { value: "not_authorised", label: "I would need a visa" },
];

const STUDENT_OPTIONS: { value: StudentChoice; label: string }[] = [
  { value: "unknown", label: "Prefer not to say" },
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
];

function toDraft(p: ProfileInput): Draft {
  return {
    education_level: p.education_level ?? "",
    field_of_study: p.field_of_study ?? "",
    years_experience: p.years_experience == null ? "" : String(Number(p.years_experience)),
    experience_summary: p.experience_summary ?? "",
    skills: [...p.skills],
    languages: p.languages.map((l) => ({ ...l })),
    preferred_countries: [...p.preferred_countries],
    career_interests: [...p.career_interests],
    work: Object.fromEntries(p.work_authorisations.map((a) => [a.country_code, a.status])),
    student: p.is_current_student == null ? "unknown" : p.is_current_student ? "yes" : "no",
  };
}

function toPayload(d: Draft): ProfileInput {
  const years = d.years_experience.trim();
  return {
    education_level: (d.education_level || null) as EducationLevel | null,
    field_of_study: d.field_of_study.trim() || null,
    years_experience: years === "" ? null : Number(years),
    experience_summary: d.experience_summary.trim() || null,
    skills: d.skills,
    languages: d.languages.map((l) => ({ language: l.language.trim(), level: l.level })),
    preferred_countries: d.preferred_countries,
    career_interests: d.career_interests,
    work_authorisations: d.preferred_countries
      .filter((c) => d.work[c] && d.work[c] !== "unknown")
      .map((c) => ({ country_code: c, status: d.work[c] as "authorised" | "not_authorised" })),
    is_current_student: d.student === "unknown" ? null : d.student === "yes",
  };
}

function missingFields(p: ProfileInput): string[] {
  return Object.keys(FIELD_LABEL).filter((k) => {
    const v = p[k as keyof ProfileInput];
    return v == null || v === "" || (Array.isArray(v) && v.length === 0);
  });
}

const input = "h-11 rounded-lg border border-field bg-surface px-3 aria-[invalid=true]:border-stop";
// min-w-0: a fieldset otherwise refuses to shrink below its widest child (overflow on phones).
const fieldset = "flex min-w-0 flex-col gap-5 rounded-[14px] border border-line bg-surface p-4 sm:p-6";

function ErrorText({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <span id={id} className="text-sm font-medium text-stop">
      {message}
    </span>
  );
}

function Segmented<T extends string>({
  name,
  value,
  options,
  onChange,
}: {
  name: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={name} className="flex flex-wrap gap-1.5">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            className={`min-h-10 rounded-lg border px-3 text-sm font-medium ${
              on ? "border-accent bg-accent text-white" : "border-field bg-surface text-ink hover:border-accent"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

function SubmitButton({ label, className = "" }: { label: string; className?: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className={`${className} flex min-h-14 w-full items-center justify-center gap-2.5 rounded-xl bg-accent px-6 text-[17px] font-semibold text-white hover:bg-accent-strong disabled:cursor-wait disabled:opacity-70`}
    >
      {pending ? "Saving…" : label}
      {!pending && <ArrowRightIcon className="size-[18px]" />}
    </button>
  );
}

type Props = { initial: ProfileInput; hasProfile: boolean };

export function ProfileForm({ initial, hasProfile }: Props) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(initial));
  const [clientErrors, setClientErrors] = useState<FieldErrors | null>(null);
  const [newCountry, setNewCountry] = useState("");
  const [active, setActive] = useState<SectionId>("education");
  // An element to focus once its tab panel is visible (hidden elements cannot take focus).
  const pendingFocus = useRef<string | null>(null);

  function goTo(section: SectionId, focusId?: string) {
    pendingFocus.current = focusId ?? null;
    setActive(section);
  }

  // After a failed submit, open the tab holding the first invalid field and focus that field.
  function showFirstError(fieldErrors: FieldErrors) {
    const first = Object.keys(fieldErrors)[0];
    if (!first) return;
    const exact = first.replace(/\./g, "-");
    const root = first.split(".")[0];
    goTo(sectionOf(first), document.getElementById(exact) ? exact : (FIELD_FOCUS_ID[root] ?? root));
  }

  const [state, formAction] = useActionState<ProfileFormState, FormData>(
    async (prev, formData) => {
      const result = await saveProfile(prev, formData);
      if (result.status === "error") showFirstError(result.errors);
      return result;
    },
    { status: "idle" },
  );

  const payload = useMemo(() => toPayload(draft), [draft]);
  const savedPayload = useMemo(() => JSON.stringify(toPayload(toDraft(initial))), [initial]);
  // Only an existing profile can have unsaved edits; a new one is unsaved by definition.
  const unsaved = hasProfile && JSON.stringify(payload) !== savedPayload;
  const submitLabel = hasProfile ? "Save changes" : "See my matches";
  const missing = missingFields(payload);
  const fieldCount = Object.keys(FIELD_LABEL).length;
  const percent = Math.round((100 * (fieldCount - missing.length)) / fieldCount);

  const serverErrors = state.status === "error" ? state.errors : {};
  const errors: FieldErrors = clientErrors ?? serverErrors;
  const formMessage = clientErrors ? "Some fields need attention." : state.status === "error" ? state.message : null;
  const errorSections = new Set(Object.keys(errors).map(sectionOf));

  // Runs after every render, so it catches the render in which the target's tab became visible.
  useEffect(() => {
    const id = pendingFocus.current;
    if (!id) return;
    const el = document.getElementById(id);
    if (el && !el.closest("[hidden]")) {
      el.focus();
      pendingFocus.current = null;
    }
  });

  function onTabKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    const index = SECTIONS.findIndex((s) => s.id === active);
    const target = {
      ArrowRight: (index + 1) % SECTIONS.length,
      ArrowLeft: (index - 1 + SECTIONS.length) % SECTIONS.length,
      Home: 0,
      End: SECTIONS.length - 1,
    }[event.key];
    if (target === undefined) return;
    event.preventDefault();
    goTo(SECTIONS[target].id, `tab-${SECTIONS[target].id}`);
  }

  const activeIndex = SECTIONS.findIndex((s) => s.id === active);
  const prevSection = SECTIONS[activeIndex - 1];
  const nextSection = SECTIONS[activeIndex + 1];

  const countryOptions = useMemo(
    () =>
      COUNTRY_CODES.map((code) => ({ code, name: countryName(code) }))
        .filter((c) => c.name !== c.code)
        .sort((a, b) => a.name.localeCompare(b.name)),
    [],
  );

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    const result = profileSchema.safeParse(payload);
    if (!result.success) {
      event.preventDefault();
      const fieldErrors = issuesToErrors(result.error.issues);
      setClientErrors(fieldErrors);
      showFirstError(fieldErrors);
      return;
    }
    setClientErrors(null);
  }

  const err = (key: string) => errors[key];
  // First error for a list field or any of its items ("skills" or "skills.3").
  const firstError = (prefix: string) =>
    Object.entries(errors).find(([k]) => k === prefix || k.startsWith(`${prefix}.`))?.[1];
  const describedBy = (key: string) => (errors[key] ? `${key}-error` : undefined);
  const workMissing = payload.preferred_countries.length > 0 && payload.work_authorisations.length === 0;

  return (
    <form
      action={formAction}
      onSubmit={onSubmit}
      noValidate
      className="flex flex-wrap items-start gap-7"
    >
      <input type="hidden" name="profile" value={JSON.stringify(payload)} />

      <div className="flex min-w-0 flex-[999_1_600px] flex-col gap-5">
        {formMessage && (
          <div role="alert" className="flex items-start gap-3 rounded-xl bg-stop-soft px-4 py-3 text-stop-strong">
            <AlertIcon className="mt-0.5 size-5" />
            <span>{formMessage}</span>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dashed border-field px-4 py-3">
          <span className="text-sm text-muted">Exploring? Fill the form with the fictional sample candidate.</span>
          <button
            type="button"
            onClick={() => {
              setDraft(toDraft(SAMPLE_PROFILE));
              setClientErrors(null);
            }}
            className="min-h-10 rounded-lg border border-field bg-surface px-3.5 text-sm font-semibold text-accent hover:border-accent"
          >
            Load sample profile
          </button>
        </div>

        <div
          role="tablist"
          aria-label="Profile sections"
          className="flex min-w-0 gap-1 overflow-x-auto rounded-[14px] border border-line bg-surface p-1.5"
        >
          {SECTIONS.map((s, i) => {
            const on = s.id === active;
            const hasError = errorSections.has(s.id);
            const notStated = s.fields.filter((f) => missing.includes(f)).length;
            return (
              <button
                key={s.id}
                id={`tab-${s.id}`}
                type="button"
                role="tab"
                aria-selected={on}
                aria-controls={`panel-${s.id}`}
                tabIndex={on ? 0 : -1}
                onClick={() => goTo(s.id)}
                onKeyDown={onTabKeyDown}
                className={`flex min-h-11 flex-1 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-[10px] px-3.5 text-sm font-semibold ${
                  on ? "bg-accent text-white" : "text-ink hover:bg-accent-soft"
                }`}
              >
                <span className={`font-mono text-xs ${on ? "text-white/80" : "text-muted"}`}>{i + 1}</span>
                {s.label}
                {hasError ? (
                  <span className={`size-2 rounded-full ${on ? "bg-white" : "bg-stop"}`}>
                    <span className="sr-only">, has errors</span>
                  </span>
                ) : notStated > 0 ? (
                  <span
                    className={`rounded-full px-1.5 font-mono text-[11px] ${on ? "bg-white/20 text-white" : "bg-warn-soft text-warn"}`}
                  >
                    {notStated}
                    <span className="sr-only"> not stated</span>
                  </span>
                ) : (
                  <span className="inline-flex">
                    <CheckIcon className={`size-4 ${on ? "text-white" : "text-ok"}`} />
                    <span className="sr-only">, complete</span>
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div role="tabpanel" id="panel-education" aria-labelledby="tab-education" hidden={active !== "education"}>
        <fieldset className={fieldset}>
          <legend className="sr-only">Education and experience</legend>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="education_level" className="text-sm font-semibold">
                Highest education
                <FieldMarker marker="required" />
              </label>
              <select
                id="education_level"
                aria-required
                value={draft.education_level}
                onChange={(e) => set("education_level", e.target.value)}
                aria-invalid={err("education_level") ? true : undefined}
                aria-describedby={describedBy("education_level")}
                className={input}
              >
                <option value="">Choose…</option>
                {EDUCATION_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {EDUCATION_LABEL[level]}
                  </option>
                ))}
              </select>
              <ErrorText id="education_level-error" message={err("education_level")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="field_of_study" className="text-sm font-semibold">
                Field of study
                <FieldMarker marker="optional" />
              </label>
              <input
                id="field_of_study"
                value={draft.field_of_study}
                onChange={(e) => set("field_of_study", e.target.value)}
                aria-invalid={err("field_of_study") ? true : undefined}
                aria-describedby={describedBy("field_of_study")}
                className={input}
              />
              <ErrorText id="field_of_study-error" message={err("field_of_study")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="years_experience" className="text-sm font-semibold">
                Years of work experience
                <FieldMarker marker="required" />
              </label>
              <input
                id="years_experience"
                aria-required
                type="number"
                inputMode="decimal"
                min={0}
                max={60}
                step={0.5}
                value={draft.years_experience}
                onChange={(e) => set("years_experience", e.target.value)}
                aria-invalid={err("years_experience") ? true : undefined}
                aria-describedby={describedBy("years_experience")}
                className={input}
              />
              <ErrorText id="years_experience-error" message={err("years_experience")} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="experience_summary" className="text-sm font-semibold">
              What you did
              <FieldMarker marker="optional" />
            </label>
            <input
              id="experience_summary"
              value={draft.experience_summary}
              onChange={(e) => set("experience_summary", e.target.value)}
              aria-invalid={err("experience_summary") ? true : undefined}
              aria-describedby={describedBy("experience_summary")}
              className={input}
            />
            <ErrorText id="experience_summary-error" message={err("experience_summary")} />
          </div>
        </fieldset>
        </div>

        <div role="tabpanel" id="panel-skills" aria-labelledby="tab-skills" hidden={active !== "skills"}>
        <fieldset className={fieldset}>
          <legend className="sr-only">Skills and languages</legend>
          <TagInput
            id="skills"
            label="Skills"
            values={draft.skills}
            onChange={(v) => set("skills", v)}
            placeholder="Add a skill, for example Data analysis"
            hint={'Press Enter to add. We match common spellings, so "MS Excel" and "Excel" count as the same skill.'}
            error={firstError("skills")}
            max={50}
            marker="required"
          />
          <div className="flex flex-col gap-2.5">
            <span className="text-sm font-semibold">
              Languages
              <FieldMarker marker="required" />
            </span>
            {draft.languages.length === 0 && (
              <p className="text-sm text-muted">No languages yet. Add at least one, with your level.</p>
            )}
            <ul className="flex flex-col gap-2">
              {draft.languages.map((lang, index) => (
                <li
                  key={index}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-line px-3.5 py-2.5"
                >
                  <div className="flex min-w-0 flex-[1_1_160px] flex-col gap-1 sm:flex-none">
                    <label htmlFor={`languages-${index}-language`} className="sr-only">
                      Language {index + 1}
                    </label>
                    <input
                      id={`languages-${index}-language`}
                      value={lang.language}
                      placeholder="Language"
                      maxLength={40}
                      onChange={(e) =>
                        set(
                          "languages",
                          draft.languages.map((l, i) => (i === index ? { ...l, language: e.target.value } : l)),
                        )
                      }
                      aria-invalid={err(`languages.${index}.language`) ? true : undefined}
                      className="h-10 w-full min-w-0 rounded-lg border border-field px-3 font-medium aria-[invalid=true]:border-stop sm:w-44"
                    />
                    <ErrorText id={`languages.${index}.language-error`} message={err(`languages.${index}.language`)} />
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Segmented
                      name={`${lang.language || "Language"} level`}
                      value={lang.level}
                      options={LANGUAGE_LEVELS.map((l) => ({ value: l, label: l[0].toUpperCase() + l.slice(1) }))}
                      onChange={(level) =>
                        set(
                          "languages",
                          draft.languages.map((l, i) => (i === index ? { ...l, level } : l)),
                        )
                      }
                    />
                    <button
                      type="button"
                      onClick={() => set("languages", draft.languages.filter((_, i) => i !== index))}
                      className="min-h-10 rounded-lg px-2.5 text-sm font-semibold text-stop hover:bg-stop-soft"
                    >
                      Remove<span className="sr-only"> {lang.language}</span>
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <ErrorText id="languages-error" message={err("languages") ?? err("form")} />
            <button
              id="languages-add"
              type="button"
              onClick={() => set("languages", [...draft.languages, { language: "", level: "professional" }])}
              disabled={draft.languages.length >= 15}
              className="min-h-11 self-start rounded-lg border border-dashed border-field bg-surface px-3.5 font-semibold text-accent"
            >
              + Add a language
            </button>
          </div>
        </fieldset>
        </div>

        <div role="tabpanel" id="panel-places" aria-labelledby="tab-places" hidden={active !== "places"}>
        <fieldset className={fieldset}>
          <legend className="sr-only">Where you want to work and what interests you</legend>
          <div className="flex flex-col gap-2.5">
            <label htmlFor="preferred_countries" className="text-sm font-semibold">
              Preferred countries
              <FieldMarker marker="optional" />
            </label>
            {draft.preferred_countries.length > 0 && (
              <ul className="flex flex-wrap gap-2">
                {draft.preferred_countries.map((code) => (
                  <li
                    key={code}
                    className="inline-flex items-center gap-2 rounded-[10px] border border-accent bg-accent-soft py-1 pl-3 pr-1 font-medium text-accent-strong"
                  >
                    <span className="font-mono text-[13px]">{code}</span>
                    {countryName(code)}
                    <button
                      type="button"
                      aria-label={`Remove ${countryName(code)}`}
                      onClick={() => set("preferred_countries", draft.preferred_countries.filter((c) => c !== code))}
                      className="flex size-8 items-center justify-center rounded-full hover:bg-white/70"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex flex-wrap gap-2">
              <select
                id="preferred_countries"
                value={newCountry}
                onChange={(e) => setNewCountry(e.target.value)}
                className={`${input} w-full min-w-0 flex-1`}
              >
                <option value="">Choose a country</option>
                {countryOptions
                  .filter((c) => !draft.preferred_countries.includes(c.code))
                  .map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.name}
                    </option>
                  ))}
              </select>
              <button
                type="button"
                disabled={!newCountry || draft.preferred_countries.length >= 20}
                onClick={() => {
                  set("preferred_countries", [...draft.preferred_countries, newCountry]);
                  setNewCountry("");
                }}
                className="min-h-11 rounded-lg border border-field bg-surface px-4 font-semibold text-accent hover:border-accent disabled:opacity-50"
              >
                Add
              </button>
            </div>
            <ErrorText id="preferred_countries-error" message={err("preferred_countries")} />
          </div>
          <TagInput
            id="career_interests"
            label="Career interests"
            values={draft.career_interests}
            onChange={(v) => set("career_interests", v)}
            placeholder="Add an interest, for example Programme support"
            error={firstError("career_interests")}
            max={20}
            marker="optional"
          />
        </fieldset>
        </div>

        <div role="tabpanel" id="panel-eligibility" aria-labelledby="tab-eligibility" hidden={active !== "eligibility"}>
        <fieldset className={fieldset}>
          <legend className="sr-only">Eligibility (optional)</legend>
          <p className="text-[15px] text-muted">
            We never assume this. If you leave it as &ldquo;Not stated&rdquo;, roles that need it are marked
            &ldquo;verify&rdquo; so you know to check.
          </p>
          <div className="flex flex-col gap-2">
            <span id="work_authorisations" tabIndex={-1} className="text-sm font-semibold">
              Right to work in your preferred countries
              <FieldMarker marker="optional" />
            </span>
            {draft.preferred_countries.length === 0 ? (
              <p className="text-sm text-muted">Add a preferred country first.</p>
            ) : (
              draft.preferred_countries.map((code) => (
                <div
                  key={code}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-line px-3.5 py-2.5"
                >
                  <span className="font-medium">
                    <span className="font-mono text-[13px] text-muted">{code}</span> {countryName(code)}
                  </span>
                  <Segmented
                    name={`Right to work in ${countryName(code)}`}
                    value={draft.work[code] ?? "unknown"}
                    options={WORK_OPTIONS}
                    onChange={(value) => set("work", { ...draft.work, [code]: value })}
                  />
                </div>
              ))
            )}
          </div>
          <div className="flex flex-col gap-2">
            <span id="is_current_student" tabIndex={-1} className="text-sm font-semibold">
              Are you currently enrolled as a student?
              <FieldMarker marker="optional" />
            </span>
            <Segmented
              name="Currently enrolled as a student"
              value={draft.student}
              options={STUDENT_OPTIONS}
              onChange={(value) => set("student", value)}
            />
          </div>
        </fieldset>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          {prevSection && (
            <button
              type="button"
              onClick={() => goTo(prevSection.id, `tab-${prevSection.id}`)}
              className="min-h-11 rounded-lg px-3 font-semibold text-muted hover:text-ink"
            >
              &larr; {prevSection.label}
            </button>
          )}
          {nextSection && (
            <button
              type="button"
              onClick={() => goTo(nextSection.id, `tab-${nextSection.id}`)}
              className="ml-auto inline-flex min-h-11 items-center gap-2 rounded-lg border border-field bg-surface px-4 font-semibold text-accent hover:border-accent"
            >
              Next: {nextSection.label} <ArrowRightIcon className="size-4" />
            </button>
          )}
        </div>

        {/* Sticky, so saving is always one click away whichever tab is open and however long it is. */}
        <div
          className="sticky bottom-3 z-10 flex flex-col gap-3 rounded-[14px] border border-line bg-surface/95 p-4 shadow-lg backdrop-blur sm:flex-row sm:items-center sm:p-5"
          style={{ marginBottom: "env(safe-area-inset-bottom)" }}
        >
          <p role="status" className="flex min-w-0 flex-1 items-start gap-2 text-sm">
            {unsaved ? (
              <>
                <AlertIcon className="mt-0.5 size-4 shrink-0 text-warn" />
                <span className="font-semibold text-warn">
                  You have unsaved changes. Your matches use your last saved profile until you save.
                </span>
              </>
            ) : (
              <span className="text-muted">
                {hasProfile
                  ? "Saving updates your matches and takes you to them."
                  : "No name or email needed. Your profile is linked to this browser only."}
              </span>
            )}
          </p>
          <SubmitButton label={submitLabel} className="shrink-0 sm:w-auto" />
        </div>
      </div>

      {/* On phones the summary comes first; the save bar sits under the form on every screen size. */}
      <aside className="order-first flex min-w-0 flex-[1_1_300px] flex-col gap-4 lg:sticky lg:top-6 lg:order-none">
        <div className="flex flex-col gap-3.5 rounded-[14px] border border-line bg-surface p-5">
          <div className="flex items-baseline justify-between">
            <span className="font-semibold">Profile strength</span>
            <span className="font-mono text-[22px] font-medium">{percent}%</span>
          </div>
          <div
            className="h-2.5 overflow-hidden rounded-full bg-track"
            role="progressbar"
            aria-valuenow={percent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Profile strength"
          >
            <div className="h-full rounded-full bg-accent transition-[width]" style={{ width: `${percent}%` }} />
          </div>
          <ul className="flex flex-col gap-2 text-sm">
            {missing.length === 0 && (
              <li className="flex gap-2 text-ok">
                <CheckIcon className="mt-0.5 size-4" />
                Everything is filled in.
              </li>
            )}
            {missing.map((field) => (
              <li key={field}>
                <button
                  type="button"
                  onClick={() => goTo(sectionOf(field), FIELD_FOCUS_ID[field] ?? field)}
                  className="flex gap-2 text-left text-warn underline-offset-2 hover:underline"
                >
                  <AlertIcon className="mt-0.5 size-4 shrink-0" />
                  {FIELD_LABEL[field]} not stated
                </button>
              </li>
            ))}
          </ul>
          {workMissing && (
            <p className="text-[13px] text-muted">
              Without right-to-work answers, roles that need it are marked &ldquo;verify&rdquo;. Scores are not
              lowered.
            </p>
          )}
        </div>
      </aside>
    </form>
  );
}

