from django.utils import timezone

from kyc.models import KYCSubmission, NotificationEvent
from kyc.state_machine import validate_transition


def transition_submission(
    submission: KYCSubmission,
    target_state: str,
    actor,
    reason: str = "",
) -> KYCSubmission:
    previous_state = submission.state
    validate_transition(previous_state, target_state)

    submission.state = target_state
    if target_state == KYCSubmission.State.SUBMITTED:
        submission.submitted_at = timezone.now()
    if target_state in {KYCSubmission.State.APPROVED, KYCSubmission.State.REJECTED}:
        submission.reviewed_at = timezone.now()
    if reason:
        submission.reviewer_reason = reason
    if actor and getattr(actor, "role", None) == "reviewer":
        submission.reviewed_by = actor
    submission.save()

    NotificationEvent.objects.create(
        merchant=submission.merchant,
        event_type=f"kyc.{target_state}",
        payload={
            "submission_id": submission.id,
            "previous_state": previous_state,
            "new_state": target_state,
            "reason": reason,
        },
    )
    return submission
