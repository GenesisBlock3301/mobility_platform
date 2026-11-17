"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ApiError, api, isNotFound, userMessage } from "@/lib/api";
import { type FieldErrors, issuesToErrors, opportunityIdSchema, profileSchema } from "@/lib/schemas";
import { clearProfileId, getProfileId, setProfileId } from "@/lib/session";
import type { Profile } from "@/lib/types";

export type ProfileFormState =
  | { status: "idle" }
  | { status: "error"; message: string; errors: FieldErrors };

function apiErrorState(error: unknown): ProfileFormState {
  if (error instanceof ApiError) {
    if (error.status === 422 && error.problem?.errors) {
      const errors: FieldErrors = {};
      for (const e of error.problem.errors) errors[e.field] ??= e.message;
      return { status: "error", message: "Some fields need attention.", errors };
    }
  }
  return {
    status: "error",
    message: userMessage(error, "We could not save your profile right now. Your answers are still here, so try again."),
    errors: {},
  };
}

export async function saveProfile(_prev: ProfileFormState, formData: FormData): Promise<ProfileFormState> {
  let raw: unknown;
  try {
    raw = JSON.parse(String(formData.get("profile") ?? ""));
  } catch {
    return { status: "error", message: "We could not read the form. Reload the page and try again.", errors: {} };
  }

  const parsed = profileSchema.safeParse(raw);
  if (!parsed.success) {
    return { status: "error", message: "Some fields need attention.", errors: issuesToErrors(parsed.error.issues) };
  }

  const existingId = await getProfileId();
  try {
    const saved: Profile = existingId
      ? await api.updateProfile(existingId, parsed.data).catch((error: unknown) => {
          // The stored profile was deleted elsewhere: start a new one.
          if (!isNotFound(error, "profile")) throw error;
          return api.createProfile(parsed.data);
        })
      : await api.createProfile(parsed.data);
    await setProfileId(saved.id);
  } catch (error) {
    return apiErrorState(error);
  }

  revalidatePath("/", "layout");
  redirect("/matches");
}

export async function deleteProfile(): Promise<void> {
  const id = await getProfileId();
  if (id) {
    try {
      await api.deleteProfile(id);
    } catch (error) {
      if (!isNotFound(error, "profile")) throw error;
    }
  }
  await clearProfileId();
  revalidatePath("/", "layout");
  redirect("/profile?deleted=1");
}

export type ShortlistResult = { ok: true } | { ok: false; message: string };

export async function toggleShortlist(opportunityId: string, save: boolean): Promise<ShortlistResult> {
  const id = await getProfileId();
  if (!id) return { ok: false, message: "Create your profile first." };
  if (!opportunityIdSchema.safeParse(opportunityId).success) {
    return { ok: false, message: "That role could not be found." };
  }
  try {
    if (save) await api.addToShortlist(id, opportunityId);
    else await api.removeFromShortlist(id, opportunityId);
  } catch (error) {
    return { ok: false, message: userMessage(error, "We could not update your shortlist. Try again.") };
  }
  revalidatePath("/", "layout");
  return { ok: true };
}
