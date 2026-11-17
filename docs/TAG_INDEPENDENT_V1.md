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

## LAB-only cards and play (implemented in the isolated preview)
- `tag_lab_cards.py`: local enrolled card aliases, teacher-maintained name/class labels, classroom assignments, separate session table.
- Private six-digit random PIN is generated on enrollment/reset, returned only once, and PBKDF2-HMAC-SHA256 hashed with a unique salt. No PIN or raw QR is stored.
- Teachers use `/tag-lab-assign.html` to register a validated card, issue/reset PIN, and assign published games to students/groups/all.
- Students use `/tag-lab-student.html` to enter card + PIN, see ONLY published assigned games, and play with a short-lived LAB session.
- DB row lock and uniqueness reject simultaneous card login; unfinished active game runs block concurrent starts, and attempts remain limited by teacher.
- Game results are written ONLY to LAB's `game_lab_runs`. All official students/XP/attempt writes are skipped in standalone mode.
- `/tag-lab-account.html` supports LAB-only teacher registration and sign-in.
- The earlier public card-to-cardRef verification API was deliberately removed: verification happens inside server handlers only.
- Older /tag-lab-students and /tag-lab-live routes are blocked, along with old official roster and game-lab-live APIs.
- GitHub Actions includes synthetic SQLite end-to-end tests and front-end JavaScript syntax checks.
- **Card functionality remains disabled on the live LAB preview until the official provider is securely enabled.** Mocked tests are not evidence that real QR codes work.

## Required before launch
- Move LAB source to a newly created independent GitHub repository (the available GitHub connector cannot create repositories).
- Test and verify LAB-local card enrollment/assignments and player UI using synthetic cards on a protected integration environment.
- Provision a shared server-side bridge secret (at least 32 characters) after provider staging verification; store only in Render secrets, not source. Rotate with deliberate cardRef remapping.
- Validate no cross-database queries, cross-origin cookies, browser-exposed secrets or official endpoints except the single card contract.
- Migrate **only** QA LAB teachers/activities/books/media/runs after backing them up, confirming mapping and verifying no raw QR/official student rows are copied. Card assignments require ref mapping.
- Test teacher login, creating games, uploading books, AI generation, saving, publishing, student cards and reports.
- Verify existing official and QA services and Neon branches remain unchanged throughout.
- Do not merge the provider into the production `main` branch until the independent LAB card flow is tested.

## Rollback
Independent preview: disable the new Render service; the original QA and official sites remain untouched.
Provider: keep its feature branch unmerged; absent server-side secret causes 503 with no card data disclosure.
