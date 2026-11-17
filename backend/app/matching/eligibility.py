"""Hard-constraint checks. These never change the fit score.

Work authorisation can never reach MET: the app has no way to confirm it, so
even a self-declared "authorised" is shown as something to verify.
"""

from app.matching.criteria import language_met
from app.matching.normalise import country_name
from app.matching.types import (
    EligibilityCheck,
    EligibilityKind,
    EligibilityStatus,
    Opportunity,
    OverallEligibility,
    Profile,
    Sponsorship,
    WorkAuthStatus,
)

VERIFY = EligibilityStatus.VERIFICATION_REQUIRED


def _language_checks(profile: Profile, opp: Opportunity) -> list[EligibilityCheck]:
    checks = []
    for req in opp.language_requirements:
        label = req.label
        if not profile.languages:
            checks.append(
                EligibilityCheck(
                    EligibilityKind.LANGUAGE,
                    VERIFY,
                    f"Requires {label}. Your profile lists no languages.",
                    ("Add your languages to your profile so this can be checked",),
                )
            )
        elif language_met(profile, req.language, req.level):
            checks.append(EligibilityCheck(EligibilityKind.LANGUAGE, EligibilityStatus.MET, f"{label}: met."))
        else:
            listed = ", ".join(lang.label for lang in profile.languages)
            checks.append(
                EligibilityCheck(
                    EligibilityKind.LANGUAGE,
                    EligibilityStatus.NOT_MET,
                    f"Requires {label}. Your profile lists {listed}.",
                )
            )
    return checks


def _work_check(profile: Profile, opp: Opportunity) -> EligibilityCheck | None:
    if not opp.requires_local_work_authorisation:
        return None
    place = country_name(opp.country_code)
    status = profile.work_status_for(opp.country_code)
    sponsorship = opp.visa_sponsorship
    confirm = f"Confirm your right to work in {place}, or check visa options for this role"
    sponsor_step = {
        Sponsorship.UNKNOWN: "Ask the employer whether they sponsor work visas",
        Sponsorship.AVAILABLE: "Confirm the terms of the visa sponsorship offered",
        Sponsorship.NOT_AVAILABLE: None,
    }[sponsorship]

    if status is WorkAuthStatus.NOT_AUTHORISED and sponsorship is Sponsorship.NOT_AVAILABLE:
        return EligibilityCheck(
            EligibilityKind.WORK_AUTHORISATION,
            EligibilityStatus.NOT_MET,
            f"You said you would need a visa for {place}, and this employer does not sponsor visas.",
        )
    if status is WorkAuthStatus.AUTHORISED:
        return EligibilityCheck(
            EligibilityKind.WORK_AUTHORISATION,
            VERIFY,
            f"You said you can work in {place}. This is self-declared: confirm it with the "
            "employer or the immigration authority.",
            (f"Have proof of your right to work in {place} ready",),
        )
    if status is WorkAuthStatus.NOT_AUTHORISED:
        offer = (
            "This employer offers visa sponsorship."
            if sponsorship is Sponsorship.AVAILABLE
            else "The employer's sponsorship policy is not stated."
        )
        return EligibilityCheck(
            EligibilityKind.WORK_AUTHORISATION,
            VERIFY,
            f"You said you would need a visa for {place}. {offer}",
            (sponsor_step,) if sponsor_step else (),
        )
    # Unknown status: never assumed either way.
    if sponsorship is Sponsorship.NOT_AVAILABLE:
        message = (
            f"Requires the right to work in {place} and does not sponsor visas. Your "
            "profile does not state your status. If you need a visa, this role is "
            "likely closed to you."
        )
    else:
        message = (
            f"Requires the right to work in {place}. Your profile does not state your "
            "status, so we have not assumed either way."
        )
    steps = tuple(s for s in (confirm, sponsor_step) if s)
    return EligibilityCheck(EligibilityKind.WORK_AUTHORISATION, VERIFY, message, steps)


def _enrolment_check(profile: Profile, opp: Opportunity) -> EligibilityCheck | None:
    if not opp.requires_current_student:
        return None
    if profile.is_current_student is True:
        return EligibilityCheck(
            EligibilityKind.ENROLMENT,
            EligibilityStatus.MET,
            "Requires current enrolment: you said you are a student.",
        )
    if profile.is_current_student is False:
        return EligibilityCheck(
            EligibilityKind.ENROLMENT,
            EligibilityStatus.NOT_MET,
            "Requires current student enrolment; you said you are not enrolled.",
        )
    return EligibilityCheck(
        EligibilityKind.ENROLMENT,
        VERIFY,
        "Requires current student enrolment. Your profile does not say whether you are enrolled.",
        ("Confirm you will be enrolled as a student for the whole internship",),
    )


def check_eligibility(profile: Profile, opp: Opportunity) -> tuple[EligibilityCheck, ...]:
    checks = _language_checks(profile, opp)
    for extra in (_work_check(profile, opp), _enrolment_check(profile, opp)):
        if extra is not None:
            checks.append(extra)
    return tuple(checks)


def overall(checks: tuple[EligibilityCheck, ...]) -> OverallEligibility:
    statuses = {c.status for c in checks}
    if EligibilityStatus.NOT_MET in statuses:
        return OverallEligibility.BLOCKED
    if VERIFY in statuses:
        return OverallEligibility.REQUIRES_VERIFICATION
    return OverallEligibility.NO_KNOWN_BLOCKERS
