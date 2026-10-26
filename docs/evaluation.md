# Evaluating NetWork

## What we measured, and why

The promise of NetWork is that adding someone takes one step and never creates a wrong contact. The first thing the app does with whatever you type is decide:

- **Just a name** ("Sarah Kim") → save it instantly, with no AI and no waiting.
- **A description** ("Lunch w Kim", "Dev Patel Snowflake") → send it to the AI, which pulls out each person, then show the result for you to confirm.

If a description is mistaken for a name, the app saves a contact called "Dev Patel Snowflake." That's the worst outcome, because it's silent and has to be cleaned up by hand. If a name is mistaken for a description, it only goes to the AI, which still returns the right person; it's just a few seconds slower.

**Primary metric:** bad contacts, meaning descriptions saved as names. Target: as close to 0 as possible.
**Secondary metrics:** overall routing accuracy, and names sent to the AI unnecessarily.

## Data

Two hand-labeled sets of realistic inputs, in [`eval/`](../eval):

| Set | Size | Used for |
|---|---|---|
| `training.json` | 35 (15 names, 20 descriptions) | Building and tuning the router |
| `heldout.json` | 40 (15 names, 25 descriptions) | Final scoring only. Written before any scoring, with different names, companies (Snowflake, PwC, Datadog…), shorthand ("w", "re"), and hard name formats ("Maria del Carmen Ruiz", "Ethan Hunt Jr.") |

Run `npm run eval` to score the router in the deployed `index.html` against both sets.

## Results

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

## Challenge case: "Jake PwC"

Two words, both capitalized, no signal words. To rules it looks exactly like "Jake Peters." Only world knowledge (that PwC is a firm) separates them. v3 still saves it as a contact named "Jake PwC."

**Safeguard added:** every instant save shows **Undo** next to the confirmation. Undo deletes the contact, puts the text back in the box, and suggests adding a little detail ("Jake from …") so the AI handles it.

**Next fix to try:** for two-word inputs where the second word is in ALL CAPS or matches a known company, ask the AI; or check the second word against company names already in your contacts.

## Other evaluations planned (not yet run)

| Question | Metric | Data needed |
|---|---|---|
| Does photo capture read sign-up sheets correctly? | Names and emails extracted correctly, per row | 10 real sign-up sheet photos with hand-typed answers |
| Are drafted messages good enough to send? | Share sent with no or light edits | The drafted text vs. what was actually sent |
| Are reminders useful or nagging? | Log vs. Not now rate per reminder type | In-app tap logs over 2 weeks |
| Does it change behavior? | Messages sent to contacts per week, before vs. after | Gmail metadata (with permission) for 5 users |
