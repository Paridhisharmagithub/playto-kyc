# EXPLAINER

## 1) The State Machine

State machine is centralized in `kyc/state_machine.py`.

```python
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
    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise ValidationError(
            {
                "code": "INVALID_TRANSITION",
                "message": f"Cannot move {current_state} to {target_state}.",
            }
        )
```

`kyc/services.py -> transition_submission()` always calls `validate_transition()` before saving. Any illegal transition raises a DRF validation error and API returns 400.

## 2) The Upload

Validation is in `kyc/serializers.py`.

```python
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

def validate_document(file_obj):
    extension = ""
    if "." in file_obj.name:
        extension = file_obj.name[file_obj.name.rfind(".") :].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError("Only PDF, JPG, and PNG files are allowed.")
    if file_obj.size > MAX_UPLOAD_SIZE:
        raise serializers.ValidationError("File size must be 5 MB or less.")
    return file_obj
```

If someone sends a 50 MB file, serializer validation fails and the API returns HTTP 400 with the validation message.

## 3) The Queue

Queue list endpoint query (`kyc/views.py`):

```python
queue = KYCSubmission.objects.filter(
    state__in=[KYCSubmission.State.SUBMITTED, KYCSubmission.State.UNDER_REVIEW]
).order_by("submitted_at", "created_at")
```

SLA flag is computed dynamically in serializer (`kyc/serializers.py`) using current time and `submitted_at`:

```python
return timezone.now() - obj.submitted_at > timedelta(hours=24)
```

I wrote it this way so:
- queue is oldest first (reviewers pick oldest item)
- `at_risk` never goes stale because it is computed on read, not stored.

## 4) The Auth

Merchant access is limited by role permission and user-scoped query:

```python
class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "merchant")

submission, _ = KYCSubmission.objects.get_or_create(merchant=request.user)
```

Because all merchant reads/writes use `request.user`, merchant A cannot fetch merchant B's submission.

## 5) The AI Audit

AI originally suggested allowing reviewer actions by directly assigning state in the view:

```python
# buggy AI suggestion
submission.state = target_state
submission.save()
```

Bug: this bypasses transition rules, so illegal moves like `submitted -> approved` could happen.

What I replaced it with:

```python
submission = transition_submission(
    submission=submission,
    target_state=target_state,
    actor=request.user,
    reason=reason,
)
```

`transition_submission()` calls centralized state validation first and logs notification events after valid state changes.
