"""Five realistic networking spreadsheets (all names made up), each with an answer key, for testing NetWork's import."""
import json, datetime as dt
from pathlib import Path
import openpyxl, xlwt
from openpyxl.styles import Font, PatternFill

OUT = Path(__file__).parent / "files"; OUT.mkdir(exist_ok=True)
D = dt.datetime
truth = []

def save_truth(file, desc, people):
    truth.append({"file": file, "desc": desc, "people": people})

# 1. A clean MBA networking tracker
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Tracker"
ws.append(["Name", "Company", "Title", "Email", "Date Met", "Notes"])
for c in ws[1]: c.font = Font(bold=True)
rows = [("Priya Shah", "Bain & Company", "Consultant", "priya.shah@bain.com", D(2026, 9, 18), "Alumni panel. Offered case practice."),
        ("Marco Ruiz", "Google", "Product Manager", "mruiz@google.com", D(2026, 10, 2), "Coffee chat about APM program"),
        ("Hannah Lee", "Stripe", "Strategy & Ops", "hannah@stripe.com", D(2026, 10, 14), "")]
for r in rows: ws.append(list(r))
ws.column_dimensions["E"].width = 14
for c in ws["E"][1:]: c.number_format = "mm/dd/yyyy"
wb.save(OUT / "1-mba-tracker.xlsx")
save_truth("1-mba-tracker.xlsx", "Clean tracker: Name, Company, Title, Email, Date Met (real Excel dates), Notes",
           [{"name": r[0], "firm": r[1], "role": r[2], "email": r[3], "date": r[4].strftime("%Y-%m-%d")} for r in rows])

# 2. Messy personal sheet: instructions tab first, title rows above the header, First/Last split, odd header names, blank rows, a TOTAL row
wb = openpyxl.Workbook(); ws0 = wb.active; ws0.title = "How to use"
ws0.append(["Keep one row per person. Update 'Last contacted' every time you reach out."])
ws = wb.create_sheet("Recruiting 2026")
ws.append(["MY RECRUITING NETWORK — FALL 2026"]); ws["A1"].font = Font(bold=True, size=14)
ws.append(["updated weekly"]); ws.append([])
ws.append(["First", "Last", "Firm", "Position", "Where we met", "Last contacted", "Next follow-up", "Priority", "Comments"])
for c in ws[4]: c.fill = PatternFill("solid", fgColor="DDEBF7")
rows = [("Daniel", "Okafor", "McKinsey", "Associate", "Consulting club mixer", D(2026, 9, 30), D(2026, 11, 3), "High", "Ask about LA office"),
        ("Sofia", "Bianchi", "Deloitte", "Senior Consultant", "Coffee chat via Jen", D(2026, 10, 9), None, "Medium", "Sent thank-you"),
        (None, None, None, None, None, None, None, None, None),
        ("Raj", "Iyer", "BCG", "Principal", "Case competition", D(2026, 8, 21), D(2026, 10, 20), "High", "Promised to send resume")]
for r in rows: ws.append(list(r))
ws.append(["TOTAL", "", "", "", "", "", "", "", "3 contacts"])
wb.save(OUT / "2-messy-recruiting.xlsx")
save_truth("2-messy-recruiting.xlsx", "Instructions tab first, title rows above header, First/Last split, Firm/Position/Where we met/Last contacted/Next follow-up, blank row, TOTAL row",
           [{"name": "Daniel Okafor", "firm": "McKinsey", "role": "Associate", "howMet": "Consulting club mixer", "date": "2026-09-30", "followUp": "2026-11-03"},
            {"name": "Sofia Bianchi", "firm": "Deloitte", "role": "Senior Consultant", "howMet": "Coffee chat via Jen", "date": "2026-10-09"},
            {"name": "Raj Iyer", "firm": "BCG", "role": "Principal", "howMet": "Case competition", "date": "2026-08-21", "followUp": "2026-10-20"}])

# 3. Old-format .xls from a career services office
wb = xlwt.Workbook(); ws = wb.add_sheet("Contacts")
date_style = xlwt.easyxf(num_format_str="M/D/YYYY")
head = ["Contact Name", "Organization", "Job Title", "E-mail Address", "Mobile", "LinkedIn URL", "Industry"]
for j, h in enumerate(head): ws.write(0, j, h)
rows = [("Aisha Bello", "Chime", "Product Lead", "aisha.bello@chime.com", "(213) 555-0119", "https://www.linkedin.com/in/aishabello/", "Fintech"),
        ("Tom Becker", "Oliver Wyman", "Manager", "tbecker@oliverwyman.com", "", "linkedin.com/in/tombecker", "Consulting")]
for i, r in enumerate(rows, 1):
    for j, v in enumerate(r): ws.write(i, j, v)
wb.save(str(OUT / "3-career-office.xls"))
save_truth("3-career-office.xls", "Old .xls: Contact Name, Organization, Job Title, E-mail Address, Mobile, LinkedIn URL, Industry",
           [{"name": r[0], "firm": r[1], "role": r[2], "email": r[3], "phone": r[4], "linkedin": r[5].replace("https://www.", "").rstrip("/"), "industry": r[6]} for r in rows])

# 4. Unusual headers the rules can't place: needs the AI fallback
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Sheet1"
ws.append(["Who I talked to", "Where they're at now", "What they do", "Reach them", "When"])
rows = [("Grace Liu", "Notion", "Designer", "grace.liu@notion.so", D(2026, 10, 1)),
        ("Ben Carter", "Meta", "Data Scientist", "bcarter@meta.com", D(2026, 9, 12))]
for r in rows: ws.append(list(r))
wb.save(OUT / "4-unusual-headers.xlsx")
save_truth("4-unusual-headers.xlsx", "Unusual headers: Who I talked to / Where they're at now / What they do / Reach them / When (needs AI)",
           [{"name": r[0], "firm": r[1], "role": r[2], "email": r[3], "date": r[4].strftime("%Y-%m-%d")} for r in rows])

# 5. A sheet with no names at all: should fail with a clear message, not import junk
wb = openpyxl.Workbook(); ws = wb.active
ws.append(["Event", "Date", "Attendance"]); ws.append(["Tech Trek", D(2026, 10, 3), 42]); ws.append(["Fall Mixer", D(2026, 9, 25), 88])
wb.save(OUT / "5-no-names.xlsx")
save_truth("5-no-names.xlsx", "No people in it (event attendance counts): should refuse clearly", [])

json.dump(truth, open(OUT / "truth.json", "w"), indent=1)
print("made", len(truth))

# 6. A normal tracker where some rows were typed as one sentence in the Name cell
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Contacts"
ws.append(["Name", "Company", "Email", "Notes"])
ws.append(["Lena Park", "Airbnb", "lena.park@airbnb.com", "Design lead"])
ws.append(["Met Jake Morales at the Bain info session, jake.morales@bain.com, follow up Friday", "", "", ""])
ws.append(["Omar Haddad", "Stripe", "ohaddad@stripe.com", ""])
ws.append(["coffee w/ Nina Shah (Deloitte, senior consultant) on 10/14 - promised to send my resume", "", "", ""])
wb.save(OUT / "6-crammed-cells.xlsx")
save_truth("6-crammed-cells.xlsx", "Normal tracker with two rows typed as one sentence in the Name cell (needs AI to split)",
           [{"name": "Lena Park", "firm": "Airbnb", "email": "lena.park@airbnb.com"},
            {"name": "Jake Morales", "firm": "Bain", "email": "jake.morales@bain.com"},
            {"name": "Omar Haddad", "firm": "Stripe", "email": "ohaddad@stripe.com"},
            {"name": "Nina Shah", "firm": "Deloitte", "role": "senior consultant", "date": "2026-10-14"}])

# 7. No columns at all: a list of sentences, like notes pasted into Excel
wb = openpyxl.Workbook(); ws = wb.active
for line in ["Priya Raman - McKinsey associate, met at MCA kickoff, priya_raman@mckinsey.com",
             "Talked to Sam Lee (Google PM) after the tech trek; send thank-you",
             "Intro from Jen: Carlos Vega, BCG principal, cvega@bcg.com, (310) 555-0142"]:
    ws.append([line])
wb.save(OUT / "7-sentences-only.xlsx")
save_truth("7-sentences-only.xlsx", "No header, each row a sentence about someone (needs AI)",
           [{"name": "Priya Raman", "firm": "McKinsey", "email": "priya_raman@mckinsey.com"},
            {"name": "Sam Lee", "firm": "Google"},
            {"name": "Carlos Vega", "firm": "BCG", "email": "cvega@bcg.com"}])
json.dump(truth, open(OUT / "truth.json", "w"), indent=1)
print("now", len(truth))
