# TeachGame Game Lab — Visual Redesign V2 (experimental)

This branch is a **non-production, teacher-only** implementation. Do not merge or deploy to the main school site before human browser QA.

## How to test

1. Deploy **this branch** to an isolated Render preview or run the existing Python server locally.
2. Sign in as an authorized teacher, then open \`/studio.html#gamelab\`.
3. Choose **saved quiz** or **quick quiz** (title, grade, question, four choices, mark the correct option).
4. Choose one of four graphical templates:
   - 🎯 Quiz: interactive multiple-choice and true/false with local scoring.
   - 🎡 Wheel: picks an unused question at random with wheel animation.
   - 🎁 Open boxes: choose a numbered box, reveal question and optionally answer.
   - 🧩 Matching: turn cards to find matching pairs, generated from match/single/true-false questions.
5. Select **play** to run a local, teacher-led game. For student live rooms, use the existing **live class** action.

## Architecture & safety

- New assets: \`teachgame-lab-v2.css\`, \`teachgame-lab-v2.js\`.
- Navigation changes: \`studio.html\`, \`app.js\`, \`studio-auth.js\`.
- Quick quiz data use the same existing teacher \`DB.quizzes\` and \`QN9_SAVE_NOW()\` cloud save confirmation.
- Source switch resets the selected quiz ID, so a quick quiz cannot accidentally overwrite a previously selected saved quiz.
- Generated games are scoped to the teacher studio and do not modify student cards, accounts, grading tables or existing live rooms.
- Existing saved quizzes remain available. Gameplay in this V2 gallery is teacher-led and **does not save per-student results**. Use the established live/solo engines for that.
- No external graphics or JS dependencies; colorful game thumbnails use pure CSS and HTML.
- Arabic right-to-left labels and contrast selectors are scoped to teacher surfaces.

## Verification before acceptance

- [ ] Run the GitHub V2 check workflow.
- [ ] Test 100% zoom on Windows, and phone layouts at 390px width.
- [ ] Create a quick quiz, save cloud, reload, confirm that original saved quizzes remain intact.
- [ ] Test all four templates with saved and newly created quizzes.
- [ ] Test mismatched game/question types and blank question validation.
- [ ] Test safe navigation back to existing generator, builder, library and live class.
- [ ] Inspect contrast and readable focus styles on all affected teacher pages.
- [ ] Review authenticated deployment environment and server logs in isolation.

### Not implemented in this first V2 branch

AI book-to-game ingestion, permanent storage of games as their own entities, per-student results for these new teacher-led templates, student real-time multiplayer game variants, and production roll-out. These need dedicated API/data/QA work, not implied by the visual UI.
