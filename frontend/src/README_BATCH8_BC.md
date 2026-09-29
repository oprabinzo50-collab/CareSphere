# CareSphere Batch 8 — Phase B + C

This batch is designed to be applied on top of the tested Batch 7 Patient 360° + Timeline state.

## Phase B — Operational UX

The existing Care Gaps, Follow-ups, Notifications and Audit Logs screens are now wrapped in a reusable `WorkflowWorkspaceFrame`.

The frame adds:
- module-specific hero/context header
- current system pulse using the existing dashboard data endpoint
- related-workspace shortcuts
- responsive layout and animated visual hierarchy

The wrapped pages remain the existing source of truth. Their existing API calls and controls are not replaced.

## Phase C — Administration

- User Management now has a View action for a richer account profile section.
- Patient-linked accounts reuse the existing protected `PatientAvatar` component.
- Staff accounts use the existing initials fallback.
- Account profile shows role, status, linked patient, account ID, created/updated timestamps and last login.
- Dashboard gains an Operational Health analytics section using the existing dashboard summary data:
  - assessment completion rate
  - active patient ratio
  - clinician review clearance rate

## Preservation rules

No database schema changes.
No backend route changes.
No authentication changes.
No AI/report-generation changes.
No Clinical Review replacement.
No changes to the existing Care Gaps, Follow-ups, Notifications or Audit Logs page implementations.
The Batch 7 Patient 360° + Timeline `ClinicalWorkspace.tsx` should remain installed.

## Files

1. `App.tsx` — cumulative Batch 7 App with Phase B/C additions.
2. `WorkflowWorkspaceFrame.tsx` — new additive reusable operational/admin frame.
3. `App_Batch8.diff` — exact diff from Batch 7 App.

## Apply

Replace your current `frontend/src/App.tsx` with the supplied `App.tsx` and add `WorkflowWorkspaceFrame.tsx` beside it under `frontend/src/`.

Do not replace your existing `ClinicalWorkspace.tsx`, workflow page implementation, API files, backend, or authentication files.

## Validation

The cumulative frontend TypeScript project check completed with zero diagnostics in the available validation environment. The workflow pages were represented by export-compatible validation stubs because the full project’s existing `WorkflowPages.tsx` file is not present in the packaged Batch 7 artifact; the production package does not replace that file.
