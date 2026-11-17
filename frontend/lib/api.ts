// Server-only client for the FastAPI service. The browser never calls the API directly.
// API_URL and INTERNAL_TOKEN are not NEXT_PUBLIC_ variables, so they never reach client code.

import { headers } from "next/headers";
import { ApiError } from "./errors";
import { getProfileId } from "./session";
import type { MatchDetail, MatchFilter, MatchPage, MatchSummary, Problem, Profile, ProfileInput } from "./types";

export { ApiError, isNotFound, userMessage } from "./errors";

const API_URL = process.env.API_URL ?? "http://localhost:8000/api/v1";
const TIMEOUT_MS = 5000;

/**
 * What the API's rate limiter counts this request against.
 *
 * The browser controls X-Forwarded-For, and Next.js keeps a client-sent value,
 * so it cannot be trusted here. Behind a reverse proxy you control, set
 * TRUST_PROXY=true: the proxy appends the real address as the last entry.
 * Otherwise use the profile cookie (one bucket per profile) or one shared
 * bucket for visitors without a profile.
 */
async function clientKey(): Promise<string> {
  if (process.env.TRUST_PROXY === "true") {
    const hops = (await headers()).get("x-forwarded-for")?.split(",") ?? [];
    const last = hops.at(-1)?.trim();
    if (last) return `ip:${last}`;
  }
  const profileId = await getProfileId();
  return profileId ? `profile:${profileId}` : "anonymous";
}

async function call<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        "content-type": "application/json",
        // Proves to the API that this request comes from the web server, so it
        // trusts x-client-key for rate limiting.
        "x-internal-token": process.env.INTERNAL_TOKEN ?? "",
        "x-client-key": await clientKey(),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    // Timeout or connection refused: treat the API as unavailable.
    throw new ApiError(503, null);
  }
  if (!response.ok) {
    let problem: Problem | null = null;
    try {
      problem = (await response.json()) as Problem;
    } catch {
      problem = null;
    }
    throw new ApiError(response.status, problem);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const enc = encodeURIComponent;

export const api = {
  createProfile: (data: ProfileInput) => call<Profile>("/profiles", "POST", data),
  getProfile: (id: string) => call<Profile>(`/profiles/${enc(id)}`),
  updateProfile: (id: string, data: ProfileInput) => call<Profile>(`/profiles/${enc(id)}`, "PUT", data),
  deleteProfile: (id: string) => call<void>(`/profiles/${enc(id)}`, "DELETE"),
  listMatches: (id: string, opts: { page?: number; pageSize?: number; filter?: MatchFilter } = {}) => {
    const query = new URLSearchParams({
      page: String(opts.page ?? 1),
      page_size: String(opts.pageSize ?? 10),
      filter: opts.filter ?? "all",
    });
    return call<MatchPage>(`/profiles/${enc(id)}/matches?${query}`);
  },
  getMatch: (id: string, opportunityId: string) =>
    call<MatchDetail>(`/profiles/${enc(id)}/matches/${enc(opportunityId)}`),
  listShortlist: (id: string) => call<MatchSummary[]>(`/profiles/${enc(id)}/shortlist`),
  shortlistIds: (id: string) => call<string[]>(`/profiles/${enc(id)}/shortlist/ids`),
  addToShortlist: (id: string, opportunityId: string) =>
    call<void>(`/profiles/${enc(id)}/shortlist/${enc(opportunityId)}`, "PUT"),
  removeFromShortlist: (id: string, opportunityId: string) =>
    call<void>(`/profiles/${enc(id)}/shortlist/${enc(opportunityId)}`, "DELETE"),
};
