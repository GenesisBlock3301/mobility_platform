"use client";

// Ticks are reminders for the user, kept only in this browser. Nothing here is sent to the server.
// They are stored by item text, so a tick never moves to a different item when the checklist changes.

import { useSyncExternalStore } from "react";
import { CheckIcon } from "./icons";

const EVENT = "mobility-checklist";
export const CHECKLIST_PREFIX = "checks:";

function key(opportunityId: string) {
  return `${CHECKLIST_PREFIX}${opportunityId}`;
}

function read(opportunityId: string): string {
  try {
    return window.localStorage.getItem(key(opportunityId)) ?? "[]";
  } catch {
    return "[]";
  }
}

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(EVENT, callback);
  };
}

function parse(raw: string): string[] {
  try {
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
  } catch {
    return [];
  }
}

type Props = { opportunityId: string; items: string[]; showStatus?: boolean };

export function VerificationChecklist({ opportunityId, items, showStatus = false }: Props) {
  const raw = useSyncExternalStore(subscribe, () => read(opportunityId), () => "[]");
  const done = new Set(parse(raw));
  const doneCount = items.filter((item) => done.has(item)).length;

  function toggle(item: string) {
    const next = new Set(done);
    if (next.has(item)) next.delete(item);
    else next.add(item);
    try {
      // Keep only ticks for items that still exist.
      window.localStorage.setItem(key(opportunityId), JSON.stringify(items.filter((i) => next.has(i))));
    } catch {
      // Storage can be unavailable (private mode); the tick just won't persist.
    }
    window.dispatchEvent(new Event(EVENT));
  }

  if (items.length === 0) {
    return <p className="text-sm text-muted">Nothing to verify for this role.</p>;
  }

  const left = items.length - doneCount;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-semibold">Before you apply</span>
        {showStatus ? (
          <span
            className={`rounded-full px-2.5 py-0.5 text-[13px] font-semibold ${
              left === 0 ? "bg-ok-soft text-ok" : "bg-warn-soft text-warn"
            }`}
          >
            {left === 0 ? "Ready to apply" : `${left} to check`}
          </span>
        ) : (
          <span className="font-mono text-sm text-muted">
            {doneCount}/{items.length}
          </span>
        )}
      </div>
      <ul className="flex flex-col gap-2">
        {items.map((item) => {
          const checked = done.has(item);
          return (
            <li key={item}>
              <button
                type="button"
                role="checkbox"
                aria-checked={checked}
                onClick={() => toggle(item)}
                className="flex min-h-11 w-full items-start gap-3 rounded-[10px] border border-line bg-surface px-3 py-2.5 text-left text-[15px] hover:border-field"
              >
                <span
                  className={`mt-px flex size-[22px] shrink-0 items-center justify-center rounded-md border-2 ${
                    checked ? "border-accent bg-accent text-white" : "border-faint bg-surface text-transparent"
                  }`}
                >
                  <CheckIcon className="size-3.5" />
                </span>
                <span className={checked ? "text-muted line-through" : ""}>{item}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-muted">Ticks are saved in this browser only, as reminders. We do not verify them.</p>
    </div>
  );
}
