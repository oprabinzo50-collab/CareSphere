# CareSphere Batch 17 — Report Release Finalization (Corrected Package)

This is the corrected, non-empty Batch 17 patch. The previous Batch 17 archive accidentally contained only empty `frontend/` and `backend/` directory entries. This archive contains the actual source files to copy into the current CareSphere project.

## What is finalized

The clinician button **Approve & Send to Patient** now performs a real backend release operation.

The release operation:
- validates the assessment/report relationship;
- blocks a report that is already rejected;
- creates or updates the existing `ClinicianReview` record with `review_status="completed"`;
- changes the report status to `completed`;
- creates or updates `PatientReportAccess` for the linked patient;
- returns the release state to the frontend.

The existing Patient Portal already exposes reports whose status is `approved` or `completed`, so the released report becomes visible in **My Health**. The patient's existing **Mark as reviewed** action remains unchanged.

## Actual files included

- `frontend/src/ReportsWorkspace.tsx`
  - uses the real release endpoint;
  - keeps the Batch 16 patient dropdown/search UX;
  - keeps the `patient={selectedPatient!}` TypeScript fix;
  - changes the action label to **Approve & Send to Patient**.

- `frontend/src/clinical.ts`
  - adds `releaseReportToPatient(...)` API helper.

- `backend/app/routes/report.py`
  - adds the real `POST /assessments/{assessment_id}/reports/{report_id}/release-to-patient` endpoint;
  - retains the existing patient-access lookup endpoint.

## Important

This patch intentionally does not replace the whole application. Copy only the three included source files over the matching files in the current project.

No report-table schema change is introduced.

## Apply in VS Code

1. Copy `frontend/src/ReportsWorkspace.tsx` to `careSphere/frontend/src/ReportsWorkspace.tsx`.
2. Copy `frontend/src/clinical.ts` to `careSphere/frontend/src/api/clinical.ts`.
3. Copy `backend/app/routes/report.py` to `careSphere/backend/app/routes/report.py`.
4. Restart the FastAPI backend.
5. Restart the Vite frontend if needed.

## Expected test

Clinician:
1. Open **Reports**.
2. Select a patient.
3. Select a completed assessment.
4. Open a generated report.
5. Add clinician guidance if desired.
6. Click **Approve & Send to Patient**.

Expected clinician result:
- report status becomes `completed`;
- a release confirmation appears;
- the button is replaced by the **Released** state.

Patient:
1. Sign in with the linked patient account.
2. Open **My Health**.
3. The released report should appear under the existing patient report/care-summary area.
4. Use **Mark as reviewed** and verify the reviewed timestamp updates.

## Validation performed

- ZIP integrity check passed.
- `py_compile` passed for the modified FastAPI route.
- `npx tsc --noEmit` passed against the staged frontend validation project.

A live browser/API/database transaction was not executed in this environment, so the final click-through should be tested against the running CareSphere backend and database.
