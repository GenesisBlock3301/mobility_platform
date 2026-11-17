// The profile ID lives only in an httpOnly cookie, so client JavaScript never sees it.

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { isNotFound } from "./errors";

const COOKIE = "profile_id";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const THIRTY_DAYS = 60 * 60 * 24 * 30;

export async function getProfileId(): Promise<string | null> {
  const value = (await cookies()).get(COOKIE)?.value;
  return value && UUID.test(value) ? value : null;
}

export async function setProfileId(id: string): Promise<void> {
  (await cookies()).set(COOKIE, id, {
    httpOnly: true,
    sameSite: "lax",
    // Secure in production. COOKIE_SECURE=false allows the local Docker demo over plain HTTP.
    secure: process.env.NODE_ENV === "production" && process.env.COOKIE_SECURE !== "false",
    path: "/",
    maxAge: THIRTY_DAYS,
  });
}

export async function clearProfileId(): Promise<void> {
  (await cookies()).delete(COOKIE);
}

/** For pages that need a profile: no cookie means no profile yet. */
export async function requireProfileId(): Promise<string> {
  const id = await getProfileId();
  if (!id) redirect("/profile");
  return id;
}

/** A 404 for the profile means it was deleted; the reset route clears the stale cookie. */
export function handleMissingProfile(error: unknown): never {
  if (isNotFound(error, "profile")) redirect("/session/reset");
  throw error;
}
