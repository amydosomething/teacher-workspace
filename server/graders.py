"""
graders.py
Grading functions for the Teacher Workspace Environment.
Contains all grading logic for the three tasks in the environment.
"""

import re
from typing import Any, Dict, List


def _find_mail_safe(inbox: List[Dict[str, Any]], mail_id: str) -> Dict[str, Any]:
    """Find an email without raising."""
    for m in inbox:
        if m["mail_id"] == mail_id:
            return m
    return None


def _get_student_math_grade(sheets: Dict[str, Any], student_id: str) -> float:
    """Return the computed final Math grade for a student, or None."""
    sheet = sheets.get("Math Gradebook", {})
    cells = sheet.get("cells", {})
    for row in range(2, 7):
        if cells.get(f"B{row}") == student_id:
            val = cells.get(f"F{row}")
            if isinstance(val, (int, float)):
                return float(val)
    return None


def _eval_formula(sheet: Dict[str, Any], formula: str) -> Any:
    """
    Evaluate a simple AVERAGE(C#,D#,E#) formula over sheet cells.
    Returns the numeric result or the original formula string if unparseable.
    """
    import re
    m = re.match(r"AVERAGE\(([^)]+)\)", formula.strip(), re.IGNORECASE)
    if not m:
        return formula  # unsupported formula — store as-is
    refs = [r.strip() for r in m.group(1).split(",")]
    values = []
    for ref in refs:
        val = sheet["cells"].get(ref)
        if isinstance(val, (int, float)):
            values.append(float(val))
    if not values:
        return formula
    return round(sum(values) / len(values), 2)


def grade_setup_new_course(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade the 'setup_new_course' task.
    
    Checks:
    1. A classroom named 'Computer Science 101' exists (+0.35)
    2. A sheet named 'CS Gradebook' exists with correct headers (+0.35)
    3. An announcement mentioning 'Welcome' exists in the new classroom (+0.30)
    """
    score = 0.0
    classrooms = state.get("classrooms", {})
    sheets = state.get("sheets", {})
    
    cs_class = next(
        (c for c in classrooms.values()
         if "Computer Science 101" in c["name"]),
        None,
    )
    if cs_class:
        score += 0.35
        # Check welcome announcement
        has_welcome = any(
            "welcome" in a["text"].lower()
            for a in cs_class["announcements"]
        )
        if has_welcome:
            score += 0.30

    # Check CS Gradebook sheet
    cs_sheet = sheets.get("CS Gradebook")
    if cs_sheet:
        headers = list(cs_sheet["cells"].values())
        required = ["Student Name", "Student ID", "Final Grade (%)"]
        if all(any(r.lower() in str(h).lower() for h in headers) for r in required):
            score += 0.35

    return {
        "score": round(min(score, 0.99), 2),
        "passed": round(min(score, 0.99), 2) >= 0.95,
        "passed_count": int(round(min(score, 0.99), 2) / 0.99 * 3) if score > 0 else 0,
        "total_criteria": 3,
        "details": {
            "has_cs_classroom": cs_class is not None,
            "has_welcome_announcement": has_welcome if cs_class else False,
            "has_cs_gradebook": cs_sheet is not None,
            "has_correct_headers": all(any(r.lower() in str(h).lower() for h in headers) for r in required) if cs_sheet else False
        }
    }


def grade_grade_and_notify(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade the 'grade_and_notify' task.
    
    Checks:
    1. Final grades computed in Math Gradebook F2:F6 (+0.30)
    2. Note added to failing student's G cell (+0.15)
    3. Emails sent to all 5 students with correct grade (+0.40)
    4. mail_002 starred (+0.15)
    """
    score = 0.0
    sheets = state.get("sheets", {})
    inbox = state.get("inbox", [])
    sent = state.get("sent", [])
    students = state.get("students", [])
    
    sheet = sheets.get("Math Gradebook", {})
    cells = sheet.get("cells", {})

    expected_grades = {
        2: 84.33,  # Alice
        3: 57.67,  # Bob   ← failing
        4: 94.67,  # Clara
        5: 70.0,   # David
        6: 88.0,   # Eva
    }

    # 1. Final grades correct
    grades_correct = sum(
        1 for row, exp in expected_grades.items()
        if isinstance(cells.get(f"F{row}"), (int, float))
        and abs(cells.get(f"F{row}") - exp) < 0.1
    )
    score += (grades_correct / 5) * 0.30

    # 2. Note in G cell of failing student (row where F < 60)
    notes = sheet.get("notes", {})
    failing_row = next(
        (row for row, exp in expected_grades.items() if exp < 60), None
    )
    has_note = failing_row and notes.get(f"G{failing_row}") is not None
    if has_note:
        score += 0.15

    # 3. Emails to students with correct grade in body
    correct_emails = 0
    for student in students:
        sent_to_student = [m for m in sent if m["to"] == student["email"]]
        if not sent_to_student:
            continue
        body = sent_to_student[-1]["body"]
        row = next(
            (r for r in range(2, 7) if cells.get(f"B{r}") == student["id"]), None
        )
        expected = expected_grades.get(row)
        if expected:
            name_ok = student["name"].split()[0].lower() in body.lower()
            numbers = [float(x) for x in re.findall(r"\d+\.?\d*", body)]
            grade_ok = any(abs(n - expected) < 0.1 for n in numbers)
            if name_ok and grade_ok:
                correct_emails += 1
    score += (correct_emails / 5) * 0.40

    # 4. Star mail_002
    mail_002 = _find_mail_safe(inbox, "mail_002")
    if mail_002 and mail_002.get("starred"):
        score += 0.15

    return {
        "score": round(min(score, 0.99), 2),
        "passed": round(min(score, 0.99), 2) >= 0.95,
        "passed_count": int(round(min(score, 0.99), 2) / 0.99 * 4) if score > 0 else 0,
        "total_criteria": 4,
        "details": {
            "grades_correct": grades_correct,
            "has_note_for_failing": has_note,
            "emails_sent_correctly": correct_emails,
            "mail_002_starred": mail_002.get("starred") if mail_002 else False
        }
    }


def grade_end_of_semester(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade the 'end_of_semester' task.
    
    Checks:
    1. Formulas set in F2:F6 of Math Gradebook (+0.20)
    2. Math Gradebook sorted by F descending (+0.10)
    3. Label 'End of Semester' created (+0.10)
    4. Report emails sent to all 5 parents (+0.25)
    5. Sent emails labelled 'End of Semester' (+0.15)
    6. Meet events created for failing students (grade < 60) (+0.20)
    """
    score = 0.0
    sheets = state.get("sheets", {})
    calendar = state.get("calendar", {})
    sent = state.get("sent", [])
    labels = state.get("labels", [])
    students = state.get("students", [])
    parents = state.get("parents", [])
    
    sheet = sheets.get("Math Gradebook", {})
    cells = sheet.get("cells", {})
    formulas = sheet.get("formulas", {})

    # 1. Formulas exist and computed values correct
    expected_grades = {
        "s001": 84.33, "s002": 57.67, "s003": 94.67, "s004": 70.0, "s005": 88.0
    }
    formula_correct = 0
    for r in range(2, 7):
        if formulas.get(f"F{r}"):
            sid = cells.get(f"B{r}")
            exp = expected_grades.get(sid)
            computed = cells.get(f"F{r}")
            if exp and isinstance(computed, (int, float)) and abs(computed - exp) < 0.1:
                formula_correct += 1
    score += (formula_correct / 5) * 0.20

    # 2. Sorted descending by F
    grades = [cells.get(f"F{r}") for r in range(2, 7)]
    numeric = [g for g in grades if isinstance(g, (int, float))]
    is_sorted_desc = len(numeric) >= 2 and all(
        numeric[i] >= numeric[i + 1] for i in range(len(numeric) - 1)
    )
    if is_sorted_desc:
        score += 0.10

    # 3. Label exists
    has_end_semester_label = "End of Semester" in labels
    if has_end_semester_label:
        score += 0.10

    # 4. Parent emails with correct parent and student names
    correct_parent_emails = 0
    for parent in parents:
        sent_to_parent = [m for m in sent if m["to"] == parent["email"]]
        if not sent_to_parent:
            continue
        body = sent_to_parent[-1]["body"]
        student = next((s for s in students if s["id"] == parent["student_id"]), None)
        if student:
            parent_name_ok = parent["name"].split()[-1].lower() in body.lower()
            student_name_ok = student["name"].split()[0].lower() in body.lower()
            if parent_name_ok and student_name_ok:
                correct_parent_emails += 1
    score += (correct_parent_emails / 5) * 0.25

    # 5. Sent emails with 'End of Semester' label
    parent_emails = {p["email"] for p in parents}
    labelled = sum(
        1 for m in sent
        if "End of Semester" in m.get("labels", [])
        and m.get("to") in parent_emails
        and "End of Semester Report" in m.get("subject", "")
    )
    score += min(labelled / 5, 1.0) * 0.15

    # 6. Meet events for failing students only — penalise spurious extras
    failing_students = [
        s for s in students
        if expected_grades.get(s["id"], 100) < 60
    ]
    passing_students = [
        s for s in students
        if expected_grades.get(s["id"], 100) >= 60
    ]

    spurious_meets = sum(
        1 for s in passing_students
        if any(
            e.get("meet_link") and s["name"].split()[0] in e.get("title", "")
            for e in calendar
        )
    )

    correct_meets = 0
    for student in failing_students:
        parent = next(
            (p for p in parents if p["student_id"] == student["id"]),
            None,
        )
        if parent:
            match = any(
                e.get("meet_link")
                and student["name"].split()[0] in e.get("title", "")
                and parent["email"] in e.get("participants", [])
                for e in calendar
            )
            if match:
                correct_meets += 1

    meet_score = (correct_meets / max(len(failing_students), 1)) - (spurious_meets * 0.20)
    score += max(meet_score, 0.0) * 0.20

    return {
        "score": round(min(score, 0.99), 2),
        "passed": round(min(score, 0.99), 2) >= 0.95,
        "passed_count": int(round(min(score, 0.99), 2) / 0.99 * 6) if score > 0 else 0,
        "total_criteria": 6,
        "details": {
            "formulas_correct": formula_correct,
            "sheet_sorted_desc": is_sorted_desc,
            "end_semester_label_created": has_end_semester_label,
            "parent_emails_correct": correct_parent_emails,
            "emails_labelled_correctly": labelled,
            "meetings_for_failing_only": correct_meets,
            "spurious_meets": spurious_meets
        }
    }


def evaluate(task_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the grader for the specified task and return a score in [0.0, 1.0].
    
    Args:
        task_name: Name of the task to grade ('setup_new_course', 'grade_and_notify', 'end_of_semester')
        state: Current environment state
        
    Returns:
        Dictionary with grading results
    """
    if task_name == "setup_new_course":
        return grade_setup_new_course(state)
    elif task_name == "grade_and_notify":
        return grade_grade_and_notify(state)
    elif task_name == "end_of_semester":
        return grade_end_of_semester(state)
    else:
        return {
            "score": 0.0,
            "passed": False,
            "passed_count": 0,
            "total_criteria": 0,
            "details": {"error": f"Unknown task: {task_name}"}
        }