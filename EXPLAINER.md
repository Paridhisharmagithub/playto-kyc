# EXPLAINER


---

## 1) The State Machine

### Where it lives
I kept all transition rules in one place: `kyc/state_machine.py`.

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
```

### How illegal transitions are blocked
Every state change goes through `transition_submission()` in `kyc/services.py`, and that always calls `validate_transition()` before save:

```python
submission = transition_submission(
    submission=submission,
    target_state=target_state,
    actor=request.user,
    reason=reason,
)
```

So if someone tries an illegal move (example: `submitted -> approved` directly), API returns 400 with a clear message.

### Why I designed it this way
- Business rules are centralized, not duplicated across views.
- Easier to test and reason about.
- Lower risk when new states/actions are added later.

---

## 2) The Upload

Upload validation is done server-side in `kyc/serializers.py` (not trusted from frontend).

```python
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

def validate_document(file_obj):
    extension = ""
    if "." in file_obj.name:
        extension = file_obj.name[file_obj.name.rfind(".") :].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError("Only PDF, JPG, and PNG files are allowed.")
    if file_obj.size > MAX_UPLOAD_SIZE:
        raise serializers.ValidationError("File size must be 5 MB or less.")

    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise serializers.ValidationError("Invalid file type. Allowed: PDF, JPG, PNG.")

    file_obj.seek(0)
    header = file_obj.read(16)
    file_obj.seek(0)

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise serializers.ValidationError("Invalid PDF file contents.")
    else:
        image = Image.open(file_obj)
        if image.format not in {"JPEG", "PNG"}:
            raise serializers.ValidationError("Invalid image format. Use JPG or PNG.")
        image.verify()
        file_obj.seek(0)

    return file_obj
```

### What happens with a 50 MB file
It fails at serializer validation (`file_obj.size > MAX_UPLOAD_SIZE`) and returns HTTP 400.

### Why this is secure enough for this scope
- Checks extension (basic guard)
- Checks content type (extra guard)
- Checks file signature/content (important guard)
- Enforces size limit on backend

So this is not only client-side validation; backend rejects bad files even if request is crafted manually.

---

## 3) The Queue

### Query used for reviewer queue
In `kyc/views.py`:

```python
queue = KYCSubmission.objects.filter(
    state__in=[KYCSubmission.State.SUBMITTED, KYCSubmission.State.UNDER_REVIEW]
).order_by("submitted_at", "created_at")
```

### SLA `at_risk` computation
In `ReviewerQueueItemSerializer`:

```python
def get_at_risk(self, obj):
    if not obj.submitted_at:
        return False
    return timezone.now() - obj.submitted_at > timedelta(hours=24)
```

### Why I wrote it this way
- Queue is oldest first, so reviewers process older submissions first.
- `at_risk` is calculated dynamically at response time.
- No stale boolean column in database.

---

## 4) The Auth

I used token auth + role-based permissions (`merchant` and `reviewer`).

### Permission checks
In `kyc/permissions.py`:

```python
class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "merchant")

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "reviewer")
```

### Merchant isolation (A cannot read B)
In merchant views, I never accept merchant ID from request. I always scope to logged-in user:

```python
submission, _ = KYCSubmission.objects.get_or_create(merchant=request.user)
```

This means merchant A can only operate on merchant A’s submission.

### Reviewer access
Reviewer endpoints use `IsReviewer` and can fetch queue/details across submissions.

---

## 5) API Design + Error Shape

All endpoints are under `/api/v1/`.
Validation is done through DRF serializers and DRF `ValidationError`.

I added a custom exception handler (`config/exceptions.py`) so errors have consistent shape:

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "details": { ... }
  }
}
```

Example: if reviewer approves an already approved submission, API returns 400 with helpful message (`Submission is already approved.`).

---

## 6) AI Audit (what AI got wrong, what I fixed)

One concrete bad suggestion from AI was to directly set state in the view:

```python
# bad suggestion
submission.state = target_state
submission.save()
```

### Why this is wrong
- Bypasses transition rules
- Allows illegal moves
- Spreads business logic into multiple views
- Easy to break authorization/business workflow accidentally

### What I replaced it with
I moved all state changes through service + centralized validation:

```python
submission = transition_submission(
    submission=submission,
    target_state=target_state,
    actor=request.user,
    reason=reason,
)
```

This ensured:
- legal transitions only
- consistent API errors
- notification logging on each valid transition

---

## Short interview-style summary

If I need to explain this quickly:

"I treated KYC state as a strict workflow and put transition rules in one file. Every state change goes through a service function, so illegal moves are blocked consistently. I validated uploads on the backend using size, extension, content type, and file signature checks. Reviewer queue is oldest-first, and SLA risk is computed dynamically (`now - submitted_at > 24h`) so it never goes stale. Auth is token + role-based, and merchant data access is scoped to `request.user`, so merchant A cannot read merchant B. I also caught and replaced AI-generated code that directly mutated state without transition checks."
