# Evaluating NetWork

Three evaluations: **(1)** deciding whether typed text is a name or a description, **(2)** reading sign-up sheet photos, and **(3)** importing spreadsheets.

## Evaluation 1: name or description?

### What we measured, and why

The promise of NetWork is that adding someone takes one step and never creates a wrong contact. The first thing the app does with whatever you type is decide:

- **Just a name** ("Sarah Kim") → save it instantly, with no AI and no waiting.
- **A description** ("Lunch w Kim", "Dev Patel Snowflake") → send it to the AI, which pulls out each person, then show the result for you to confirm.

If a description is mistaken for a name, the app saves a contact called "Dev Patel Snowflake." That's the worst outcome, because it's silent and has to be cleaned up by hand. If a name is mistaken for a description, it only goes to the AI, which still returns the right person; it's just a few seconds slower.

**Primary metric:** bad contacts, meaning descriptions saved as names. Target: as close to 0 as possible.
**Secondary metrics:** overall routing accuracy, and names sent to the AI unnecessarily.

### Data

Two hand-labeled sets of realistic inputs, in [`eval/`](../eval):

| Set | Size | Used for |
|---|---|---|
| `training.json` | 35 (15 names, 20 descriptions) | Building and tuning the router |
| `heldout.json` | 40 (15 names, 25 descriptions) | Final scoring only. Written before any scoring, with different names, companies (Snowflake, PwC, Datadog…), shorthand ("w", "re"), and hard name formats ("Maria del Carmen Ruiz", "Ethan Hunt Jr.") |

Run `npm run eval` to score the router in the deployed `index.html` against both sets.

### Results

| Version | Training: routed right | Held-out: routed right | Held-out: bad contacts |
|---|---|---|---|
| **v1 baseline** (original rules) | 31/35 (89%) | 27/40 (68%) | **13 of 25** |
| **v2** (added a word list, including common company names, after seeing training errors) | 35/35 (100%) | 31/40 (78%) | **9 of 25** |
| **v3 shipped** (general signal words + send 3–4 plain words to the AI) | 32/35 (91%) | **38/40 (95%)** | **1 of 25** |

**What we learned.** v2 scored 100% on the data it was tuned on and only 78% on new data. It had memorized company names ("Google", "Bain") instead of learning the pattern. The held-out set exposed that.

v3 changes the approach rather than the word list:
1. It only uses words that signal a description regardless of company: verbs ("bumped," "spoke"), meeting words ("lunch," "zoom"), job titles ("VP," "recruiter," "AE"), and shorthand ("w," "re").
2. **Workflow change:** three or four plain capitalized words ("Rachel Green Ralph Lauren" vs. "Maria del Carmen Ruiz") can't be told apart by rules, so those go to the AI instead of being guessed. Known name particles ("van," "del," "Jr.") still save instantly.

The trade-off is that a few real names, like "Dr. Amir Haddad," now take the slower AI path. That costs a few seconds but never creates a wrong contact.

### Challenge case: "Jake PwC"

Two words, both capitalized, no signal words. To rules it looks exactly like "Jake Peters." Only world knowledge (that PwC is a firm) separates them. v3 still saves it as a contact named "Jake PwC."

**Safeguard added:** every instant save shows **Undo** next to the confirmation. Undo deletes the contact, puts the text back in the box, and suggests adding a little detail ("Jake from …") so the AI handles it.

**Next fix to try:** for two-word inputs where the second word is in ALL CAPS or matches a known company, ask the AI; or check the second word against company names already in your contacts.

## Evaluation 2: reading sign-up sheet photos

**What we measured.** Tap **Photo**, snap a sign-up sheet, and NetWork reads everyone on it. The costly mistakes here are different from typing: a **wrong email** (your follow-up bounces), a **made-up field** (the AI fills in a company that wasn't written), or a **crossed-out row added as a person**. Missing a person is less bad; you can type them in.

**Data.** 10 sign-up sheet photos, made to look like real phone photos: handwriting fonts (a different writer per row), tilt, perspective, shadows, uneven light, blur, and noise. Every name and email is made up, and each photo has a hand-written answer key: 83 people, 73 emails, 77 companies, 4 phone numbers, and 4 LinkedIn URLs. They get harder from 1 to 10:

| # | What makes it hard |
|---|---|
| 1 | Nothing: clean printed table |
| 2 | Neat handwriting |
| 3 | Mixed handwriting, tilted, photographed at an angle |
| 4 | Blanks: some people skipped email or company; one wrote only "Hope" |
| 5 | A crossed-out entry rewritten on the next line, and a scribbled, unreadable row |
| 6 | Dim, blurry, noisy photo |
| 7 | Different columns: company first, then phone and LinkedIn |
| 8 | 20 people on one sheet, small writing |
| 9 | Accented names: José Muñoz, Siobhán Ní Bhriain, Łukasz Nowak, Nguyễn Thị Lan, Zoë Müller |
| 10 | Free-form notebook page, no table, a different separator on each line |

Plus a **stress set**: sheets 3, 8, and 9 made much worse (heavy blur, dark, low resolution) to find the breaking point. A person would struggle to read them too.

**How.** [`eval/photo-run.js`](../eval/photo-run.js) runs each photo through `extractPhoto`, the same function the Photo button uses, on the live site with the live model. [`eval/photo-score.mjs`](../eval/photo-score.mjs) (`npm run eval:photos`) scores the results against the answer keys. Names and emails must match exactly, accents included; companies ignore punctuation and case. Raw results for every run are in [`eval/photos/`](../eval/photos).

### Results

| | Normal sheets, run 1 | Normal sheets, run 2 (repeatability) | Normal sheets, **with flags** | Stress, before | Stress, **with flags** |
|---|---|---|---|---|---|
| People found | 83/83 | 83/83 | 83/83 | 21/38 | 21/38 |
| Names exactly right | 83/83 | 83/83 | 83/83 | 20/38 | 21/38 |
| Emails exactly right | 72/73 | 71/73 | 71/73 | 11/21 read | 16/21 read |
| Companies right | 77/77 | 77/77 | 77/77 | 15/19 read | 17/19 read |
| Crossed-out or unreadable rows added | 0/2 | 0/2 | 0/2 | – | – |
| Made-up fields | 0 | 0 | 0 | 0 | 0 |
| **Wrong values flagged "Hard to read"** | 0/1 | – | **2/2** | 0/6 | **6/6** |
| Correct values flagged anyway | 0 | – | 12 of 239 (5%) | 0 | 26 of 54 |
| Median time per photo | 4.5 s | 4.5 s | 5.6 s | 9.8 s | 10 s |

**What we learned.**
1. **On ordinary photos it's nearly perfect.** It found all 83 people, got every name right (accents included), and read 97–99% of emails exactly. It never invented a field, and it skipped the crossed-out entry and the scribbled row instead of adding them. It even noticed that "Andre" wrote an email starting "andrew" and said to check it.
2. **The only misses are tiny dots in emails** (derek.johnson → derekjohnson, its.jnj → itsjnj). Small, but a wrong email means a bounced follow-up.
3. **On bad photos it mostly skips rather than guesses.** It read 21 of 38 people and reported the rest as unreadable. On the worst photo it read no one, and the app asks for a sharper photo. But it still made **6 confident wrong reads** ("Alex" read as "Max", "Whitfield" as "Whitefield", Hulu as Meta), and nothing on the review card warned you.

**Improvement: "Hard to read" flags.** We changed the photo step so the AI marks every field it isn't sure of, and the review card highlights that person with an amber "Hard to read: check the email against the photo" note. Results:
- **Every wrong value was flagged**: 2 of 2 on normal sheets, 6 of 6 on the stress set.
- **Cost on normal photos:** 5% of correct values flagged unnecessarily, mostly on the dim photo (sheet 6), where a second look is reasonable anyway.
- **Cost on stress photos:** about half of correct values flagged. That's the right trade when the photo is barely readable.
- Accuracy didn't drop. On the stress set it was a bit better (16 of 21 emails right vs. 11), likely because being asked to doubt itself made it read more carefully.

**Challenge case: the missing dot.** "derek.johnson@snowflake.com" in small handwriting reads as "derekjohnson@snowflake.com". It looks perfectly plausible, and a person skimming the card would likely miss it too. Before this change it saved silently. Now it carries a flag, so the person checks it against the photo before saving.

**Limits of this test.** The photos are synthetic: handwriting fonts are neater and more consistent than real handwriting, so the normal-sheet numbers are best-case. The next step is the same scoring on 10 real sheets from club events.

## Evaluation 3: importing spreadsheets

People usually keep contacts in Excel, with their own column names. We built 5 test files with answer keys ([`eval/spreadsheets/`](../eval/spreadsheets)) and check every field of every person ([`eval/tests/spreadsheet-import.test.mjs`](../eval/tests/spreadsheet-import.test.mjs), `npm test`):

| File | What makes it hard | Without AI | With AI |
|---|---|---|---|
| 1-mba-tracker.xlsx | Nothing: Name, Company, Title, Email, Date Met (real Excel dates), Notes | ✓ | ✓ |
| 2-messy-recruiting.xlsx | "How to use" tab first, title rows above the header, First/Last split, "Firm", "Position", "Where we met", "Last contacted", "Next follow-up", a blank row, a TOTAL row | ✓ | ✓ |
| 3-career-office.xls | Old Excel format; "Contact Name", "Organization", "E-mail Address", "Mobile", "LinkedIn URL" | ✓ | ✓ |
| 4-unusual-headers.xlsx | "Who I talked to", "Where they're at now", "What they do", "Reach them", "When" | Asks for a Name header (correct) | ✓ mapped by AI |
| 5-no-names.xlsx | Event attendance counts, no people | Refused (correct) | Refused (correct) |

**Safeguards.** Before importing, the preview shows how each column was read ("Firm → Company") so the person can catch a wrong match. When the AI maps the columns, the preview says so. And if the AI picks a "name" column full of dates or numbers, the import is refused (tested by giving it a deliberately wrong mapping). Reminders for imported people stay off unless the person turns them on, but follow-up dates from the sheet still show up on Today.

## Other evaluations planned (not yet run)

| Question | Metric | Data needed |
|---|---|---|
| Does photo capture hold up on real handwriting? | Same scoring as Evaluation 2 | 10 real sign-up sheets from club events, with hand-typed answer keys |
| Does Get an intro suggest the right people? | Share of suggested introducers the user actually asks; share of asks that get a yes | Logged asks ("I sent it") over a month |
| Are drafted messages good enough to send? | Share sent with no or light edits | The drafted text vs. what was actually sent |
| Are reminders useful or nagging? | Log vs. Not now rate per reminder type | In-app tap logs over 2 weeks |
| Does it change behavior? | Messages sent to contacts per week, before vs. after | Gmail metadata (with permission) for 5 users |
