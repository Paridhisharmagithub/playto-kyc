from rest_framework.exceptions import ValidationError

from kyc.models import KYCSubmission


ALLOWED_TRANSITIONS = {
    KYCSubmission.State.DRAFT: {KYCSubmission.State.SUBMITTED},
    KYCSubmission.State.SUBMITTED: {KYCSubmission.State.UNDER_REVIEW},
    KYCSubmission.State.UNDER_REVIEW: {
        KYCSubmission.State.APPROVED,
        KYCSubmission.State.REJECTED,
        KYCSubmission.State.MORE_INFO_REQUESTED,
    },
    KYCSubmission.State.MORE_INFO_REQUESTED: {KYCSubmission.State.SUBMITTED},
    KYCSubmission.State.APPROVED: set(),
    KYCSubmission.State.REJECTED: set(),
}


def validate_transition(current_state: str, target_state: str) -> None:
    if current_state == target_state:
        if current_state == KYCSubmission.State.APPROVED:
            message = "Submission is already approved."
        elif current_state == KYCSubmission.State.REJECTED:
            message = "Submission is already rejected."
        else:
            message = f"Submission is already in {current_state} state."
        raise ValidationError({"code": "INVALID_TRANSITION", "message": message})

    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise ValidationError(
            {
                "code": "INVALID_TRANSITION",
                "message": f"Cannot move {current_state} to {target_state}.",
            }
        )
