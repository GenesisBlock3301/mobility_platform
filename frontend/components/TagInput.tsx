"use client";

import { useState } from "react";
import { FieldMarker, type Marker } from "./FieldMarker";

type Props = {
  id: string;
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder: string;
  hint?: string;
  error?: string;
  max: number;
  marker?: Marker;
};

export function TagInput({ id, label, values, onChange, placeholder, hint, error, max, marker }: Props) {
  const [text, setText] = useState("");
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;

  function add() {
    const value = text.trim().replace(/\s+/g, " ").slice(0, 60);
    if (!value) return;
    if (!values.some((v) => v.toLowerCase() === value.toLowerCase()) && values.length < max) {
      onChange([...values, value]);
    }
    setText("");
  }

  return (
    <div className="flex flex-col gap-2.5">
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
        <FieldMarker marker={marker} />
      </label>
      {values.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label={`${label} added`}>
          {values.map((value) => (
            <li
              key={value}
              className="inline-flex items-center gap-1 rounded-full bg-accent-soft py-1 pl-3 pr-1 text-sm font-medium text-accent-strong"
            >
              {value}
              <button
                type="button"
                onClick={() => onChange(values.filter((v) => v !== value))}
                className="flex size-8 items-center justify-center rounded-full text-lg leading-none hover:bg-white/70"
                aria-label={`Remove ${value}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <input
          id={id}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              add();
            }
          }}
          placeholder={placeholder}
          maxLength={60}
          aria-describedby={[hint ? hintId : "", error ? errorId : ""].join(" ").trim() || undefined}
          aria-required={marker === "required" ? true : undefined}
          aria-invalid={error ? true : undefined}
          className="h-11 min-w-0 flex-1 rounded-lg border border-dashed border-field bg-surface px-3"
        />
        <button
          type="button"
          onClick={add}
          className="min-h-11 rounded-lg border border-field bg-surface px-4 font-semibold text-accent hover:border-accent"
        >
          Add
        </button>
      </div>
      {hint && (
        <span id={hintId} className="text-[13px] text-muted">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="text-sm font-medium text-stop">
          {error}
        </span>
      )}
    </div>
  );
}
