"""
world.py
World state management for the Teacher Workspace Environment.
Handles all the state data for classrooms, sheets, emails, etc.
"""

from typing import Any, Dict, List
from uuid import uuid4


def _build_initial_state() -> Dict[str, Any]:
    """
    Returns a fresh workspace state seeded with realistic data.

    The data is intentionally interdependent:
    - Students in Classroom match rows in the Sheets gradebook.
    - Unread emails in Gmail are from those same students / parents.
    - A parent-teacher meeting already exists in Calendar for reference.
    """
    students = [
        {"name": "Alice Johnson",  "email": "alice@students.school.edu",  "id": "s001"},
        {"name": "Bob Martinez",   "email": "bob@students.school.edu",    "id": "s002"},
        {"name": "Clara Singh",    "email": "clara@students.school.edu",  "id": "s003"},
        {"name": "David Lee",      "email": "david@students.school.edu",  "id": "s004"},
        {"name": "Eva Patel",      "email": "eva@students.school.edu",    "id": "s005"},
    ]
    parents = [
        {"name": "Mr. Johnson",  "email": "johnson.parent@gmail.com",  "student_id": "s001"},
        {"name": "Mrs. Martinez","email": "martinez.parent@gmail.com", "student_id": "s002"},
        {"name": "Mr. Singh",    "email": "singh.parent@gmail.com",    "student_id": "s003"},
        {"name": "Mrs. Lee",     "email": "lee.parent@gmail.com",      "student_id": "s004"},
        {"name": "Mr. Patel",    "email": "patel.parent@gmail.com",    "student_id": "s005"},
    ]

    # ── Google Classroom ───────────────────────────────────────────────────
    classrooms = {
        "cls_math101": {
            "class_id":      "cls_math101",
            "name":          "Mathematics 101",
            "section":       "Grade 10 - Section A",
            "description":   "Algebra and geometry fundamentals",
            "students":      students,
            "announcements": [
                {
                    "announcement_id": "ann_001",
                    "text":  "Midterm exam next Friday. Please review chapters 4–6.",
                    "date":  "2025-03-10",
                    "comments": [],
                }
            ],
        },
        "cls_sci101": {
            "class_id":      "cls_sci101",
            "name":          "Science 101",
            "section":       "Grade 10 - Section A",
            "description":   "Introduction to physics and chemistry",
            "students":      students,
            "announcements": [],
        },
    }

    # ── Google Sheets gradebook ────────────────────────────────────────────
    # One sheet per subject; rows mirror the student list above.
    sheets = {
        "Math Gradebook": {
            "sheet_name": "Math Gradebook",
            "cells": {
                "A1": "Student Name", "B1": "Student ID",
                "C1": "Midterm (%)",  "D1": "Assignment 1 (%)",
                "E1": "Assignment 2 (%)", "F1": "Final Grade (%)",
                "G1": "Notes",

                "A2": "Alice Johnson",  "B2": "s001",
                "C2": 78, "D2": 85, "E2": 90, "F2": "", "G2": "",

                "A3": "Bob Martinez",   "B3": "s002",
                "C3": 55, "D3": 60, "E3": 58, "F3": "", "G3": "Needs extra support",

                "A4": "Clara Singh",    "B4": "s003",
                "C4": 92, "D4": 95, "E4": 97, "F4": "", "G4": "",

                "A5": "David Lee",      "B5": "s004",
                "C5": 70, "D5": 72, "E5": 68, "F5": "", "G5": "",

                "A6": "Eva Patel",      "B6": "s005",
                "C6": 88, "D6": 91, "E6": 85, "F6": "", "G6": "",
            },
            "notes": {},
            "formulas": {},
        },
        "Science Gradebook": {
            "sheet_name": "Science Gradebook",
            "cells": {
                "A1": "Student Name", "B1": "Student ID",
                "C1": "Lab Report (%)", "D1": "Quiz 1 (%)",
                "E1": "Final Grade (%)", "F1": "Notes",

                "A2": "Alice Johnson",  "B2": "s001", "C2": 80, "D2": 76, "E2": "", "F2": "",
                "A3": "Bob Martinez",   "B3": "s002", "C3": 50, "D3": 48, "E3": "", "F3": "Absent for quiz",
                "A4": "Clara Singh",    "B4": "s003", "C4": 95, "D4": 98, "E4": "", "F4": "",
                "A5": "David Lee",      "B5": "s004", "C5": 74, "D5": 70, "E5": "", "F5": "",
                "A6": "Eva Patel",      "B6": "s005", "C6": 85, "D6": 88, "E6": "", "F6": "",
            },
            "notes": {},
            "formulas": {},
        },
    }

    # ── Gmail inbox ────────────────────────────────────────────────────────
    # Mix of student questions, parent concerns, and admin mail.
    inbox = [
        {
            "mail_id":   "mail_001",
            "from":      "bob@students.school.edu",
            "from_name": "Bob Martinez",
            "to":        "teacher@school.edu",
            "subject":   "Help with algebra homework",
            "body":      "Hi, I am struggling with quadratic equations. Can we schedule extra help?",
            "date":      "2025-03-12",
            "read":      False,
            "starred":   False,
            "important": False,
            "spam":      False,
            "labels":    [],
            "category":  "",
        },
        {
            "mail_id":   "mail_002",
            "from":      "martinez.parent@gmail.com",
            "from_name": "Mrs. Martinez",
            "to":        "teacher@school.edu",
            "subject":   "Bob's performance concern",
            "body":      "Dear Teacher, Bob seems to be struggling lately. Could we arrange a meeting?",
            "date":      "2025-03-11",
            "read":      False,
            "starred":   False,
            "important": False,
            "spam":      False,
            "labels":    [],
            "category":  "",
        },
        {
            "mail_id":   "mail_003",
            "from":      "principal@school.edu",
            "from_name": "Principal Adams",
            "to":        "teacher@school.edu",
            "subject":   "End-of-semester grade submission deadline",
            "body":      "Please submit all final grades by April 15th via the gradebook system.",
            "date":      "2025-03-10",
            "read":      True,
            "starred":   False,
            "important": True,
            "spam":      False,
            "labels":    [],
            "category":  "admin",
        },
        {
            "mail_id":   "mail_004",
            "from":      "alice@students.school.edu",
            "from_name": "Alice Johnson",
            "to":        "teacher@school.edu",
            "subject":   "Assignment submission",
            "body":      "Hi! I have submitted my Assignment 2. Please let me know if you received it.",
            "date":      "2025-03-09",
            "read":      True,
            "starred":   False,
            "important": False,
            "spam":      False,
            "labels":    [],
            "category":  "",
        },
        {
            "mail_id":   "mail_005",
            "from":      "noreply@schoolads.com",
            "from_name": "School Ads",
            "to":        "teacher@school.edu",
            "subject":   "Buy discounted stationery!",
            "body":      "Click here for amazing deals on school supplies!",
            "date":      "2025-03-08",
            "read":      False,
            "starred":   False,
            "important": False,
            "spam":      False,
            "labels":    [],
            "category":  "",
        },
    ]

    # ── Gmail sent + drafts ────────────────────────────────────────────────
    sent = []
    drafts = []
    labels = ["Important", "Parents", "Students", "Admin"]

    # ── Google Calendar ────────────────────────────────────────────────────
    calendar = [
        {
            "event_id":     "evt_001",
            "title":        "Staff Meeting",
            "date":         "2025-03-15",
            "time":         "09:00",
            "participants": ["teacher@school.edu", "principal@school.edu"],
            "meet_link":    None,
            "description":  "Monthly staff sync",
        },
        {
            "event_id":     "evt_002",
            "title":        "Math 101 Midterm Exam",
            "date":         "2025-03-20",
            "time":         "10:00",
            "participants": ["teacher@school.edu"] + [s["email"] for s in students],
            "meet_link":    None,
            "description":  "Midterm covering chapters 4-6",
        },
    ]

    return {
        "classrooms": classrooms,
        "sheets":     sheets,
        "inbox":      inbox,
        "sent":       sent,
        "drafts":     drafts,
        "labels":     labels,
        "calendar":   calendar,
        "students":   students,
        "parents":    parents,
    }


class WorldState:
    """
    Manages the world state for the Teacher Workspace Environment.
    Contains all data for classrooms, sheets, emails, calendar events, etc.
    """
    
    def __init__(self):
        self.reset()
        self.action_log = []  # Track all actions taken in the environment

    def reset(self):
        """Reset the world state to the initial state."""
        self.state = _build_initial_state()
        self.action_log = []

    def update_state(self, new_state: Dict[str, Any]):
        """Update the entire state with a new state dictionary."""
        self.state = new_state

    def get_classrooms(self) -> Dict[str, Any]:
        """Get all classrooms."""
        return self.state.get("classrooms", {})

    def get_classroom(self, class_id: str) -> Dict[str, Any]:
        """Get a specific classroom by ID."""
        return self.state["classrooms"].get(class_id)

    def get_sheets(self) -> Dict[str, Any]:
        """Get all sheets."""
        return self.state.get("sheets", {})

    def get_sheet(self, sheet_name: str) -> Dict[str, Any]:
        """Get a specific sheet by name."""
        return self.state["sheets"].get(sheet_name)

    def get_inbox(self) -> List[Dict[str, Any]]:
        """Get all inbox emails."""
        return self.state.get("inbox", [])

    def get_sent(self) -> List[Dict[str, Any]]:
        """Get all sent emails."""
        return self.state.get("sent", [])

    def get_calendar(self) -> List[Dict[str, Any]]:
        """Get all calendar events."""
        return self.state.get("calendar", [])

    def get_labels(self) -> List[str]:
        """Get all labels."""
        return self.state.get("labels", [])

    def get_students(self) -> List[Dict[str, Any]]:
        """Get all students."""
        return self.state.get("students", [])

    def get_parents(self) -> List[Dict[str, Any]]:
        """Get all parents."""
        return self.state.get("parents", [])

    def find_mail(self, mail_id: str) -> Dict[str, Any]:
        """Find an email in inbox or sent; raise TypeError if not found."""
        for m in self.state["inbox"] + self.state["sent"]:
            if m["mail_id"] == mail_id:
                return m
        raise TypeError(f"Mail '{mail_id}' not found in inbox or sent.")

    def find_mail_safe(self, mail_id: str) -> Dict[str, Any]:
        """Find an email without raising."""
        for m in self.state["inbox"]:
            if m["mail_id"] == mail_id:
                return m
        return None

    def get_student_math_grade(self, student_id: str) -> float:
        """Return the computed final Math grade for a student, or None."""
        sheet = self.state["sheets"].get("Math Gradebook", {})
        cells = sheet.get("cells", {})
        for row in range(2, 7):
            if cells.get(f"B{row}") == student_id:
                val = cells.get(f"F{row}")
                if isinstance(val, (int, float)):
                    return float(val)
        return None

    def eval_formula(self, sheet: Dict[str, Any], formula: str) -> Any:
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

    def add_action_to_log(self, action: Dict[str, Any]):
        """Add an action to the action log."""
        self.action_log.append(action)