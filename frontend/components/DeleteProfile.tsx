"use client";

import { useState } from "react";
import { useFormStatus } from "react-dom";
import { deleteProfile } from "@/app/actions";
import { CHECKLIST_PREFIX } from "./VerificationChecklist";

function ConfirmButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="min-h-11 rounded-lg bg-stop px-4 text-sm font-semibold text-white disabled:opacity-60"
    >
      {pending ? "Deleting…" : "Yes, delete everything"}
    </button>
  );
}

// Checklist ticks live in this browser; remove them along with the profile.
function clearChecklistTicks() {
  try {
    for (const key of Object.keys(window.localStorage)) {
      if (key.startsWith(CHECKLIST_PREFIX)) window.localStorage.removeItem(key);
    }
  } catch {
    // Storage unavailable: nothing was stored.
  }
}

export function DeleteProfile() {
  const [confirming, setConfirming] = useState(false);
  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="min-h-11 self-start px-1 text-sm font-semibold text-stop underline"
      >
        Delete my profile
      </button>
    );
  }
  return (
    <form action={deleteProfile} onSubmit={clearChecklistTicks} className="flex flex-col gap-3 rounded-xl border border-stop/40 bg-stop-soft p-4">
      <p className="text-sm text-stop-strong">
        This permanently removes your profile and your shortlist. It cannot be undone.
      </p>
      <div className="flex flex-wrap gap-2">
        <ConfirmButton />
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="min-h-11 rounded-lg border border-field bg-surface px-4 text-sm font-semibold"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
