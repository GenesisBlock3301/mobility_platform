// API errors and the checks every caller needs. Kept apart from api.ts so that
// session.ts can use them without a circular import.

import type { Problem } from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly problem: Problem | null,
  ) {
    super(problem?.detail ?? `The API returned ${status}`);
    this.name = "ApiError";
  }
}

/** True for a 404. Pass a resource to check which one is missing. */
export function isNotFound(error: unknown, resource?: "profile" | "opportunity"): error is ApiError {
  return (
    error instanceof ApiError &&
    error.status === 404 &&
    (resource === undefined || error.problem?.resource === resource)
  );
}

/** Text that is safe to show the user: the API's own message for 4xx, else the fallback. */
export function userMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.problem?.detail) {
    return error.problem.detail;
  }
  return fallback;
}
