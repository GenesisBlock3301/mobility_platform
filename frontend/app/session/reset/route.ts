// Clears a profile cookie that points at a deleted profile, then starts over.
// Server Components cannot change cookies, so they redirect here instead.
// It is a GET (a redirect target), so it only clears the cookie after the API
// confirms the profile is gone: a link from another site cannot log anyone out.

import { redirect } from "next/navigation";
import { api, isNotFound } from "@/lib/api";
import { clearProfileId, getProfileId } from "@/lib/session";

async function profileIsGone(id: string): Promise<boolean> {
  try {
    await api.getProfile(id);
    return false;
  } catch (error) {
    if (isNotFound(error, "profile")) return true;
    throw error;
  }
}

export async function GET() {
  const id = await getProfileId();
  if (id && (await profileIsGone(id))) await clearProfileId();
  redirect("/profile");
}
