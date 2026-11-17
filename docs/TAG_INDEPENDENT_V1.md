# TAG INDEPENDENT V1 — Separation plan and safety checklist

## Product decision (17 Nov 2026)
- **TAG official:** exams, competitions, official student cards, school analytics.
- **TAG LAB:** educational games, books, AI, Game Mixer, private activity library/results.
- The ONLY inter-platform contract is a student-card lookup; there is NO shared teacher login, game database, class leaderboard, result store or UI.
- Students keep their original physical QR/cards. Never regenerate the physical codes to complete this migration.
- Official production (`main`) and the existing QA service must not be changed by the isolated deployment.

## Infrastructure created
- Dedicated Neon project `tag-lab-independent-v1` / database `taglab`, Frankfurt. **No student or teacher data copied.**
- Separate Render free service `tag-lab-independent-v1`, branch `feature/tag-independent-v1-lab`, manual deploy, with `TAG_LAB_ONLY_MODE=1`.
- The service temporarily reads an isolated feature branch of the original GitHub repository. A second repository is still a follow-up task; it is NOT yet a fully separate source repository.
- Read-only baseline: teacher_count=0, student_count=0, activity_count=0.
- Keep original Render services untouched. Never connect this service to the production DATABASE_URL.

## Card-only contract (designed; requires activation)
Official provider, opt-in only: `POST /api/tag-independent/card/resolve`.
LAB consumer, opt-in: `POST /api/tag-independent/card/verify`.
- Server-to-server `Authorization: Bearer <TAG_CARD_BRIDGE_SECRET>`, minimum 32 chars, HTTPS, no browser CORS.
- Request: `{"card":"<physical QR token or short card code>"}`.
- Provider response: `{"ok":true,"version":1,"cardRef":"tg1_<40 hexadecimal chars>"}`.
- `cardRef` is a stable HMAC alias of the student record; do NOT return student name, school, teacher ID, marks, scores, XP, or raw QR.
- Do not copy or persist raw QR values in the LAB database.
- Unknown cards: 403. Unconfigured bridge: 503. Rate-limit both endpoints.
- Provider code is on `feature/tag-independent-v1-card-provider`, NOT on the live official `main` branch.
- **Do not activate until end-to-end tests on isolated, synthetic data pass.** The official endpoint is currently unavailable, and so independent LAB card verification deliberately returns 503.

## LAB local roster and assignment model (next coding phase)
1. Each independent LAB teacher authenticates to LAB's own teacher table.
2. Enroll a card with its physical code: the server verifies via the official provider, then stores `cardRef` under the LAB teacher, plus a **LAB-local** display label and a LAB-local group. This is not a copy of the official roster.
3. Teacher assigns a published LAB game to one or more enrolled `cardRef` values or LAB-local groups.
4. Student opens LAB's card games, submits existing physical code, receives a short lived LAB session; lookup resolves to `cardRef` and displays only assigned published games.
5. Record LAB results solely in the dedicated LAB database; never credit or read official grades, XP or results.
6. Existing code `game_lab_pro.student_catalog`, `game_lab_pro.assign` and `game_lab_api.start` still assume a shared `students` table. Refactor all three **before** enabling cards; do not silently fall back to a local fake student table.

## Required before launch
- Move LAB source to a newly created independent GitHub repository (the available GitHub connector cannot create repositories).
- Implement the LAB-local card enrollments, group assignments and activity start authorization.
- Provision and rotate the server-side bridge secret on both services; store only in Render secrets.
- Validate no cross-database queries, cross-origin cookies, browser-exposed secrets or official endpoints except the single card contract.
- Migrate **only** QA LAB teachers/activities/books/media/runs after backing them up, confirming mapping and verifying no raw QR/official student rows are copied. Card assignments require ref mapping.
- Test teacher login, creating games, uploading books, AI generation, saving, publishing, student cards and reports.
- Verify existing official and QA services and Neon branches remain unchanged throughout.
- Do not merge the provider into the production `main` branch until the independent LAB card flow is tested.

## Rollback
Independent preview: disable the new Render service; the original QA and official sites remain untouched.
Provider: keep its feature branch unmerged; absent server-side secret causes 503 with no card data disclosure.
