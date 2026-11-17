import type { Metadata } from "next";
import { DeleteProfile } from "@/components/DeleteProfile";
import { CheckIcon } from "@/components/icons";
import { ProfileForm } from "@/components/ProfileForm";
import { api } from "@/lib/api";
import { EMPTY_PROFILE, SAMPLE_PROFILE } from "@/lib/sample";
import { getProfileId, handleMissingProfile } from "@/lib/session";
import type { ProfileInput } from "@/lib/types";

export const metadata: Metadata = { title: "Your profile" };

type Props = { searchParams: Promise<{ sample?: string; deleted?: string }> };

export default async function ProfilePage({ searchParams }: Props) {
  const params = await searchParams;
  const id = await getProfileId();

  let initial: ProfileInput = params.sample === "1" ? SAMPLE_PROFILE : EMPTY_PROFILE;
  if (id) {
    const profile = await api.getProfile(id).catch(handleMissingProfile);
    initial = {
      ...profile,
      years_experience: profile.years_experience == null ? null : Number(profile.years_experience),
    };
  }

  return (
    <main className="mx-auto flex max-w-[1180px] flex-col gap-7 px-4 pb-16 pt-10 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-1.5">
          <h1 className="font-display text-4xl font-semibold tracking-tight">Your career profile</h1>
          <p className="text-muted">
            {id
              ? "Change anything, then save to update your matches."
              : "Tell us what you can do and where you would like to work. Only the fields marked * are required; leave anything you are unsure of empty."}
          </p>
        </div>
        {id && (
          <span className="inline-flex items-center gap-2 rounded-full bg-ok-soft px-3 py-1.5 text-sm font-semibold text-ok">
            <CheckIcon className="size-4" /> Profile saved
          </span>
        )}
      </div>

      {params.deleted === "1" && !id && (
        <p role="status" className="rounded-xl bg-ok-soft px-4 py-3 text-ok-strong">
          Your profile and shortlist were deleted.
        </p>
      )}

      <ProfileForm initial={initial} hasProfile={Boolean(id)} />

      {id && (
        <section className="flex flex-col gap-2 border-t border-line pt-6" aria-labelledby="delete-heading">
          <h2 id="delete-heading" className="font-display text-lg font-semibold">
            Your data
          </h2>
          <p className="max-w-[60ch] text-sm text-muted">
            We store only what you entered above, with no name or email. Deleting removes your profile and your
            shortlist straight away.
          </p>
          <DeleteProfile />
        </section>
      )}
    </main>
  );
}
