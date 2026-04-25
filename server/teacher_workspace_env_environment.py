"""
teacher_workspace_env_environment.py
Teacher Workspace Environment Implementation.

Simulates a Google Workspace environment (Classroom + Sheets + Gmail +
Calendar/Meet) for a teacher's daily administrative workflow.

All state is pure Python — no external APIs, no databases, no network calls.
"""
import re
from uuid import uuid4
from typing import Any, Dict, List, Optional
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import TeacherAction, TeacherObservation
except ImportError:
    from models import TeacherAction, TeacherObservation

# Import tools and graders from separate modules
from .tools import TOOL_DEFINITIONS
from .graders import evaluate as run_grader
from .world import WorldState
from .tasks import get_task, get_all_tasks, get_task_names


# ── Read-only tools (reward = 0.0) ─────────────────────────────────────────
READ_TOOLS = {
    "list_classrooms", "get_classroom", "list_announcements",
    "list_sheets", "get_cells",
    "list_inbox", "read_mail", "search_mail",
    "list_events", "get_event",
}

# ── Per-task action whitelist ───────────────────────────────────────────────
def _build_allowed_actions(state: dict) -> dict:
    student_emails = {s["email"] for s in state["students"]}
    parent_emails  = {p["email"] for p in state["parents"]}

    def _get_failing_student_ids() -> set:
        """
        Get student IDs whose expected grade is < 60.
        Uses raw scores (C, D, E columns) directly so sort order
        of F column doesn't affect the result.
        """
        mg = state.get("sheets", {}).get("Math Gradebook", {})
        cells = mg.get("cells", {})
        failing = set()
        for row in range(2, 7):
            sid = cells.get(f"B{row}")
            c   = cells.get(f"C{row}")
            d   = cells.get(f"D{row}")
            e   = cells.get(f"E{row}")
            if sid and all(isinstance(v, (int, float)) for v in [c, d, e]):
                avg = (c + d + e) / 3
                if avg < 60:
                    failing.add(sid)
        return failing

    def _get_failing_student_names() -> list:
        failing_ids = _get_failing_student_ids()
        return [
            s["name"].split()[0]
            for s in state["students"]
            if s["id"] in failing_ids
        ]

    def _failing_student_rows() -> list:
        """
        Returns row numbers where the student is failing.
        Uses raw C/D/E scores, not F (which may be reordered by sort).
        """
        mg = state.get("sheets", {}).get("Math Gradebook", {})
        cells = mg.get("cells", {})
        failing_ids = _get_failing_student_ids()
        rows = []
        for row in range(2, 7):
            sid = cells.get(f"B{row}")
            if sid in failing_ids:
                rows.append(row)
        return rows

    def is_valid_note_cell(params: dict) -> bool:
        if params.get("sheet_name") != "Math Gradebook":
            return False
        cell = params.get("cell", "")
        if not cell.startswith("G"):
            return False
        try:
            row = int(cell[1:])
        except ValueError:
            return False
        # FIX 1: use raw C/D/E scores, not _failing_student_rows() which
        # depended on F being populated first — causing valid add_note calls
        # to be penalized when F column hadn't been written yet.
        mg = state.get("sheets", {}).get("Math Gradebook", {})
        cells = mg.get("cells", {})
        sid = cells.get(f"B{row}")
        c = cells.get(f"C{row}")
        d = cells.get(f"D{row}")
        e = cells.get(f"E{row}")
        if not (sid and all(isinstance(v, (int, float)) for v in [c, d, e])):
            return False
        return (c + d + e) / 3 < 60

    def is_valid_grade_cell(params: dict) -> bool:
        if params.get("sheet_name") != "Math Gradebook":
            return False
        cell = params.get("cell", "")
        if not cell.startswith("F"):
            return False
        try:
            row = int(cell[1:])
            return 2 <= row <= 6
        except ValueError:
            return False

    def is_valid_formula_cell(params: dict) -> bool:
        """set_formula allowed in Task 2 only for F2:F6 in Math Gradebook."""
        if params.get("sheet_name") != "Math Gradebook":
            return False
        cell = params.get("cell", "")
        if not cell.startswith("F"):
            return False
        try:
            row = int(cell[1:])
            return 2 <= row <= 6
        except ValueError:
            return False

    def is_failing_meet(params: dict) -> bool:
        mg = state.get("sheets", {}).get("Math Gradebook", {})
        cells = mg.get("cells", {})
        failing_names = set()
        for row in range(2, 7):
            c = cells.get(f"C{row}")
            d = cells.get(f"D{row}")
            e = cells.get(f"E{row}")
            name = cells.get(f"A{row}", "")
            if all(isinstance(v, (int, float)) for v in [c, d, e]):
                if (c + d + e) / 3 < 60:
                    failing_names.add(name.split()[0])
        title = params.get("title", "")
        return any(name in title for name in failing_names)

    return {
        "setup_new_course": {
            "create_classroom":    lambda p: "Computer Science 101" in p.get("name", ""),
            "create_sheet":        lambda p: p.get("sheet_name") == "CS Gradebook",
            "create_announcement": lambda p: True,
        },
        "grade_and_notify": {
            "update_cell": is_valid_grade_cell,
            "set_formula": is_valid_formula_cell,  # ← added
            "add_note":    is_valid_note_cell,
            "send_mail":   lambda p: p.get("to") in student_emails,
            "star_mail":   lambda p: p.get("mail_id") == "mail_002",
        },
        "end_of_semester": {
            "set_formula":       lambda p: p.get("sheet_name") == "Math Gradebook",
            "sort_range":        lambda p: (
                p.get("sheet_name") == "Math Gradebook" and
                p.get("column") == "F"
            ),
            "create_label":      lambda p: p.get("name") == "End of Semester",
            "send_mail":         lambda p: p.get("to") in parent_emails,
            "assign_label": lambda p: (
                p.get("label") == "End of Semester"
                and any(
                    m.get("to") in parent_emails
                    and "End of Semester Report" in m.get("subject", "")
                    and m.get("mail_id") == p.get("mail_id")
                    for m in state.get("sent", [])
                )
            ),
            "create_meet_event": is_failing_meet,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class TeacherWorkspaceEnvironment(Environment):
    """
    Teacher Workspace RL Environment.

    The agent acts as a teacher managing a school day through four simulated
    Google Workspace apps. All state lives in-memory as Python dicts.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state:    Optional[Dict[str, Any]] = None
        self._ep_state: Optional[State]          = None
        self._task:     Optional[Dict[str, Any]] = None
        self._rewards:  List[float]              = []
        self._rewarded: Dict[str, bool]          = {}
        self.world:     WorldState               = WorldState()

    # ──────────────────────────────────────────────────────────────────────
    # OpenEnv interface
    # ──────────────────────────────────────────────────────────────────────

    def reset(self, task_name: str = "setup_new_course", **kwargs) -> TeacherObservation:
        """Reset workspace to a fresh seeded state and load the requested task."""
        self.world.reset()
        self._state = self.world.state
        self._ep_state = State(episode_id=str(uuid4()), step_count=0)
        self._task = get_task(task_name)
        self._rewards = []
        self._last_action  = None   # add this
        self._repeat_count = 0  

        return self._make_obs(
            success=True,
            result={"message": "Workspace ready. Read the task prompt and begin."},
            reward=0.0,
            done=False,
        )

    def step(self, action: TeacherAction) -> TeacherObservation:  # type: ignore[override]
        """Route the action to the correct handler and return an observation."""
        if self._state is None:
            raise RuntimeError("Call reset() before step().")

        self._ep_state.step_count += 1

        tool = action.tool_name
        params = action.params or {}

            # Penalise repeated identical read calls (infinite loop behavior)
        if not hasattr(self, '_last_action'):
            self._last_action = None
            self._repeat_count = 0

        if tool == self._last_action and tool in READ_TOOLS:
            self._repeat_count += 1
            if self._repeat_count >= 2:
                obs = self._make_obs(
                    success=False,
                    result=None,
                    error=f"Repeated read '{tool}' with no write in between — unproductive loop.",
                    reward=-0.05,
                    done=False,
                )
                self._rewards.append(-0.05)
                return obs
        else:
            self._repeat_count = 0
        self._last_action = tool

        # Dispatch
        handler = getattr(self, f"_tool_{tool}", None)
        if handler is None:
            obs = self._make_obs(
                success=False,
                result=None,
                error=f"Unknown tool: {tool}",
                reward=-0.05,
                done=False,
            )
            self._rewards.append(-0.05)
            return obs

        try:
            result, reward, done = handler(**params)

            audit_penalty = self._audit_action(tool, params)
            if audit_penalty < 0:
                # Override reward to 0 first, then apply penalty
                # This prevents partial_reward canceling out the audit
                reward = audit_penalty

            self._rewards.append(reward)
            return self._make_obs(
                success=True,
                result=result,
                reward=reward,
                done=done,
                error=(
                    f"Unnecessary or incorrect action: "
                    f"{abs(audit_penalty):.2f} penalty applied"
                ) if audit_penalty < 0 else None,
            )
        except TypeError as e:
            obs = self._make_obs(
                success=False,
                result=None,
                error=f"Bad params for {tool}: {e}",
                reward=-0.05,
                done=False,
            )
            self._rewards.append(-0.05)
            return obs

    @property
    def state(self) -> State:
        if self._ep_state is None:
            raise RuntimeError("Call reset() first.")
        return self._ep_state

    # ──────────────────────────────────────────────────────────────────────
    # Observation builder
    # ──────────────────────────────────────────────────────────────────────

    def _make_obs(
        self,
        success: bool,
        result: Any,
        reward: float,
        done: bool,
        error: Optional[str] = None,
    ) -> TeacherObservation:
        s = self._state or {}
        return TeacherObservation(
            success=success,
            result=result,
            error=error,
            classrooms=s.get("classrooms", {}),
            sheets=s.get("sheets", {}),
            inbox=s.get("inbox", []),
            sent=s.get("sent", []),
            drafts=s.get("drafts", []),
            calendar=s.get("calendar", []),
            labels=s.get("labels", []),
            students=s.get("students", []),
            parents=s.get("parents", []),
            step=self._ep_state.step_count if self._ep_state else 0,
            task_name=self._task["name"] if self._task else "",
            task_prompt=self._task["prompt"] if self._task else "",
            done=done,
            reward=reward,
        )

    # ══════════════════════════════════════════════════════════════════════
    # ── GOOGLE CLASSROOM HANDLERS ─────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    def _tool_list_classrooms(self) -> tuple:
        """Read – returns all classrooms. reward=0.0"""
        classrooms = [
            {"class_id": cid, "name": c["name"], "section": c["section"]}
            for cid, c in self._state["classrooms"].items()
        ]
        return classrooms, 0.0, False

    def _tool_get_classroom(self, class_id: str) -> tuple:
        """Read – returns full details of one classroom."""
        cls = self._state["classrooms"].get(class_id)
        if cls is None:
            raise TypeError(f"Classroom '{class_id}' not found.")
        return cls, 0.0, False

    def _tool_list_announcements(self, class_id: str) -> tuple:
        """Read – returns announcements for a classroom."""
        cls = self._state["classrooms"].get(class_id)
        if cls is None:
            raise TypeError(f"Classroom '{class_id}' not found.")
        return cls["announcements"], 0.0, False

    def _tool_create_classroom(self, name: str, section: str,
                                description: str = "") -> tuple:
        """Write – creates a new classroom."""
        class_id = f"cls_{uuid4().hex[:8]}"
        self._state["classrooms"][class_id] = {
            "class_id":      class_id,
            "name":          name,
            "section":       section,
            "description":   description,
            "students":      self._state["students"],  # same cohort
            "announcements": [],
        }
        reward = self._partial_reward(0.25, "create_classroom")
        done   = self._check_done()
        return {"class_id": class_id, "name": name}, reward, done

    def _tool_delete_classroom(self, class_id: str) -> tuple:
        """Write – deletes a classroom. Penalises if class has students."""
        cls = self._state["classrooms"].pop(class_id, None)
        if cls is None:
            raise TypeError(f"Classroom '{class_id}' not found.")
        penalty = -0.1 if cls.get("students") else 0.0
        return {"deleted": class_id}, penalty, False

    def _tool_create_announcement(self, class_id: str, text: str) -> tuple:
        """Write – posts an announcement to a classroom."""
        cls = self._state["classrooms"].get(class_id)
        if cls is None:
            raise TypeError(f"Classroom '{class_id}' not found.")
        ann_id = f"ann_{uuid4().hex[:6]}"
        announcement = {
            "announcement_id": ann_id,
            "text":            text,
            "date":            "2025-03-13",
            "comments":        [],
        }
        cls["announcements"].append(announcement)
        reward = self._partial_reward(0.2, "create_announcement")
        done   = self._check_done()
        return {"announcement_id": ann_id}, reward, done

    def _tool_delete_announcement(self, class_id: str,
                                   announcement_id: str) -> tuple:
        """Write – deletes an announcement."""
        cls = self._state["classrooms"].get(class_id)
        if cls is None:
            raise TypeError(f"Classroom '{class_id}' not found.")
        before = len(cls["announcements"])
        cls["announcements"] = [
            a for a in cls["announcements"]
            if a["announcement_id"] != announcement_id
        ]
        if len(cls["announcements"]) == before:
            raise TypeError(f"Announcement '{announcement_id}' not found.")
        return {"deleted": announcement_id}, 0.05, False

    def _tool_add_comment(self, announcement_id: str, text: str) -> tuple:
        """Write – adds a comment to an announcement."""
        for cls in self._state["classrooms"].values():
            for ann in cls["announcements"]:
                if ann["announcement_id"] == announcement_id:
                    comment = {
                        "comment_id": f"cmt_{uuid4().hex[:6]}",
                        "text":       text,
                        "date":       "2025-03-13",
                    }
                    ann["comments"].append(comment)
                    return {"comment_id": comment["comment_id"]}, 0.05, False
        raise TypeError(f"Announcement '{announcement_id}' not found.")

    def _tool_delete_comment(self, announcement_id: str,
                              comment_id: str) -> tuple:
        """Write – deletes a comment."""
        for cls in self._state["classrooms"].values():
            for ann in cls["announcements"]:
                if ann["announcement_id"] == announcement_id:
                    before = len(ann["comments"])
                    ann["comments"] = [
                        c for c in ann["comments"]
                        if c["comment_id"] != comment_id
                    ]
                    if len(ann["comments"]) == before:
                        raise TypeError(f"Comment '{comment_id}' not found.")
                    return {"deleted": comment_id}, 0.0, False
        raise TypeError(f"Announcement '{announcement_id}' not found.")

    # ══════════════════════════════════════════════════════════════════════
    # ── GOOGLE SHEETS HANDLERS ────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    def _tool_list_sheets(self) -> tuple:
        """Read – returns names of all sheets."""
        return list(self._state["sheets"].keys()), 0.0, False

    def _tool_get_cells(self, sheet_name: str,
                         cell_range: str = "A1:Z100") -> tuple:
        """Read – returns cells from a sheet. cell_range is informational."""
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")
        return sheet["cells"], 0.0, False

    def _tool_create_sheet(self, sheet_name: str,
                            headers: Optional[List[str]] = None) -> tuple:
        """Write – creates a new spreadsheet sheet with optional headers."""
        if sheet_name in self._state["sheets"]:
            raise TypeError(f"Sheet '{sheet_name}' already exists.")
        cells: Dict[str, Any] = {}
        if headers:
            for i, h in enumerate(headers):
                col = chr(ord("A") + i)
                cells[f"{col}1"] = h
        self._state["sheets"][sheet_name] = {
            "sheet_name": sheet_name,
            "cells":      cells,
            "notes":      {},
            "formulas":   {},
        }
        reward = self._partial_reward(0.2, "create_sheet")
        done   = self._check_done()
        return {"sheet_name": sheet_name, "headers": headers}, reward, done

    def _tool_delete_sheet(self, sheet_name: str) -> tuple:
        """Write – deletes a sheet."""
        if sheet_name not in self._state["sheets"]:
            raise TypeError(f"Sheet '{sheet_name}' not found.")
        del self._state["sheets"][sheet_name]
        return {"deleted": sheet_name}, 0.0, False

    def _tool_update_cell(self, sheet_name: str, cell: str,
                           value: Any) -> tuple:
        """Write – sets the value of a single cell."""
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")
        sheet["cells"][cell] = value
        reward = self._partial_reward(0.05, f"update_cell_{sheet_name}_{cell}")
        done   = self._check_done()
        return {"cell": cell, "value": value}, reward, done

    def _tool_add_note(self, sheet_name: str, cell: str, note: str) -> tuple:
        """Write – adds a text note to a cell."""
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")
        sheet["notes"][cell] = note
        reward = self._partial_reward(0.1, f"add_note_{sheet_name}_{cell}")
        done   = self._check_done()
        return {"cell": cell, "note": note}, reward, done

    def _tool_set_formula(self, sheet_name: str, cell: str,
                           formula: str) -> tuple:
        """
        Write – stores a formula string and computes a numeric result.
        Supports AVERAGE(C#,D#,E#) over cells in the same sheet.
        """
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")

        computed = self.world.eval_formula(sheet, formula)
        sheet["formulas"][cell] = formula
        sheet["cells"][cell]    = computed

        reward = self._partial_reward(0.1, f"set_formula_{sheet_name}_{cell}")
        done   = self._check_done()
        return {"cell": cell, "formula": formula, "computed": computed}, reward, done

    def _tool_sort_range(self, sheet_name: str, column: str,
                          ascending: bool = False) -> tuple:
        """Write – sorts data rows (rows 2+) by a given column."""
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")

        cells = sheet["cells"]
        # Determine how many data rows exist
        row_num = 2
        rows = []
        while f"A{row_num}" in cells or f"{column}{row_num}" in cells:
            row = {}
            for col_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                key = f"{col_char}{row_num}"
                if key in cells:
                    row[col_char] = cells[key]
            rows.append(row)
            row_num += 1

        sort_val = lambda r: (r.get(column, 0) if isinstance(r.get(column, 0), (int, float)) else 0)
        rows.sort(key=sort_val, reverse=not ascending)

        # Write sorted rows back
        for i, row in enumerate(rows, start=2):
            for col_char, val in row.items():
                cells[f"{col_char}{i}"] = val

        reward = self._partial_reward(0.1, f"sort_{sheet_name}_{column}")
        done   = self._check_done()
        return {"sorted_by": column, "ascending": ascending, "rows": len(rows)}, reward, done

    def _tool_filter_range(self, sheet_name: str, column: str,
                            operator: str, value: Any) -> tuple:
        """Read – returns rows where column <op> value. Does not mutate state."""
        sheet = self._state["sheets"].get(sheet_name)
        if sheet is None:
            raise TypeError(f"Sheet '{sheet_name}' not found.")

        cells = sheet["cells"]
        matching = []
        row_num = 2
        while f"A{row_num}" in cells or f"{column}{row_num}" in cells:
            cell_val = cells.get(f"{column}{row_num}")
            try:
                cell_num = float(cell_val) if cell_val is not None else None
                ref_num  = float(value)
                match = (
                    (operator == ">"  and cell_num is not None and cell_num >  ref_num) or
                    (operator == ">=" and cell_num is not None and cell_num >= ref_num) or
                    (operator == "<"  and cell_num is not None and cell_num <  ref_num) or
                    (operator == "<=" and cell_num is not None and cell_num <= ref_num) or
                    (operator == "==" and cell_num is not None and cell_num == ref_num)
                )
            except (TypeError, ValueError):
                match = (operator == "==" and str(cell_val) == str(value))

            if match:
                row = {}
                for col_char in "ABCDEFG":
                    k = f"{col_char}{row_num}"
                    if k in cells:
                        row[col_char] = cells[k]
                row["_row"] = row_num
                matching.append(row)
            row_num += 1

        return matching, 0.0, False

    # ══════════════════════════════════════════════════════════════════════
    # ── GMAIL HANDLERS ────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    def _tool_list_inbox(self) -> tuple:
        """Read – returns all inbox emails (summary view)."""
        summary = [
            {
                "mail_id": m["mail_id"],
                "from":    m["from_name"],
                "subject": m["subject"],
                "date":    m["date"],
                "read":    m["read"],
                "starred": m["starred"],
            }
            for m in self._state["inbox"]
        ]
        return summary, 0.0, False

    def _tool_read_mail(self, mail_id: str) -> tuple:
        """Read – returns full content of one email and marks it as read."""
        mail = self.world.find_mail(mail_id)
        mail["read"] = True
        return mail, 0.0, False

    def _tool_search_mail(self, query: str) -> tuple:
        """Read – searches inbox by subject or sender (case-insensitive)."""
        q = query.lower()
        results = [
            m for m in self._state["inbox"]
            if q in m["subject"].lower()
            or q in m["from"].lower()
            or q in m["from_name"].lower()
            or q in m["body"].lower()
        ]
        return results, 0.0, False

    def _tool_create_draft(self, to: str, subject: str, body: str) -> tuple:
        """Write – saves an email draft."""
        draft_id = f"dft_{uuid4().hex[:6]}"
        draft = {
            "draft_id": draft_id,
            "to":       to,
            "subject":  subject,
            "body":     body,
            "date":     "2025-03-13",
        }
        self._state["drafts"].append(draft)
        return {"draft_id": draft_id}, 0.05, False

    def _tool_send_mail(self, to: str, subject: str, body: str) -> tuple:
        """Write – sends an email. Also adds it to sent box."""
        mail_id = f"mail_{uuid4().hex[:6]}"
        mail = {
            "mail_id": mail_id,
            "from":    "teacher@school.edu",
            "to":      to,
            "subject": subject,
            "body":    body,
            "date":    "2025-03-13",
            "labels":  [],
        }
        self._state["sent"].append(mail)
        reward = self._partial_reward(0.1, f"send_mail_{to}")
        done   = self._check_done()
        return {"mail_id": mail_id, "to": to}, reward, done

    def _tool_categorise_mail(self, mail_id: str, category: str) -> tuple:
        """Write – sets the category field of an email."""
        mail = self.world.find_mail(mail_id)
        mail["category"] = category
        reward = self._partial_reward(0.05, f"categorise_{mail_id}")
        done   = self._check_done()
        return {"mail_id": mail_id, "category": category}, reward, done

    def _tool_star_mail(self, mail_id: str) -> tuple:
        """Write – stars an email."""
        mail = self.world.find_mail(mail_id)
        mail["starred"] = True
        reward = self._partial_reward(0.1, f"star_{mail_id}")
        done   = self._check_done()
        return {"mail_id": mail_id, "starred": True}, reward, done

    def _tool_mark_unread(self, mail_id: str) -> tuple:
        """Write – marks an email as unread."""
        mail = self.world.find_mail(mail_id)
        mail["read"] = False
        return {"mail_id": mail_id, "read": False}, 0.05, False

    def _tool_mark_important(self, mail_id: str) -> tuple:
        """Write – marks an email as important."""
        mail = self.world.find_mail(mail_id)
        mail["important"] = True
        reward = self._partial_reward(0.05, f"important_{mail_id}")
        done   = self._check_done()
        return {"mail_id": mail_id, "important": True}, reward, done

    def _tool_mark_spam(self, mail_id: str) -> tuple:
        """Write – marks an email as spam."""
        mail = self.world.find_mail(mail_id)
        mail["spam"] = True
        reward = self._partial_reward(0.1, f"spam_{mail_id}")
        done   = self._check_done()
        return {"mail_id": mail_id, "spam": True}, reward, done

    def _tool_delete_mail(self, mail_id: str) -> tuple:
        """Write – deletes an email from inbox."""
        before = len(self._state["inbox"])
        self._state["inbox"] = [
            m for m in self._state["inbox"] if m["mail_id"] != mail_id
        ]
        if len(self._state["inbox"]) == before:
            raise TypeError(f"Mail '{mail_id}' not found.")
        return {"deleted": mail_id}, 0.0, False

    def _tool_create_label(self, name: str) -> tuple:
        """Write – creates a new Gmail label."""
        if name in self._state["labels"]:
            raise TypeError(f"Label '{name}' already exists.")
        self._state["labels"].append(name)
        reward = self._partial_reward(0.1, f"create_label_{name}")
        done   = self._check_done()
        return {"label": name}, reward, done

    def _tool_assign_label(self, mail_id: str, label: str) -> tuple:
        """Write – assigns a label to a sent or inbox email."""
        # Search both inbox and sent
        mail = None
        for m in self._state["inbox"] + self._state["sent"]:
            if m["mail_id"] == mail_id:
                mail = m
                break
        if mail is None:
            raise TypeError(f"Mail '{mail_id}' not found.")
        if label not in self._state["labels"]:
            raise TypeError(f"Label '{label}' does not exist. Create it first.")
        if label not in mail["labels"]:
            mail["labels"].append(label)
        # FIX 2: only give reward if the label is one the active task actually requires.
        # Prevents spurious reward for off-task labels like "Grades" in grade_and_notify,
        # or labelling auto-generated meet-invite emails in end_of_semester.
        task_name = self._task["name"] if self._task else ""
        required_labels = {
            "end_of_semester": "End of Semester",
        }
        required_label = required_labels.get(task_name)

        # For end_of_semester, also verify the mail being labelled is an actual
        # parent report email (sent box, correct subject) — not a meet invite.
        if required_label and label == required_label:
            sent_mail = next((m for m in self._state["sent"] if m["mail_id"] == mail_id), None)
            parent_emails = {p["email"] for p in self._state["parents"]}
            if (
                sent_mail
                and sent_mail.get("to") in parent_emails
                and "End of Semester Report" in sent_mail.get("subject", "")
            ):
                reward = self._partial_reward(0.05, f"assign_label_{mail_id}_{label}")
            else:
                reward = 0.0
        else:
            reward = 0.0
        done   = self._check_done()
        return {"mail_id": mail_id, "label": label}, reward, done

    # ══════════════════════════════════════════════════════════════════════
    # ── CALENDAR / MEET HANDLERS ──────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    def _tool_list_events(self) -> tuple:
        """Read – returns all calendar events."""
        return self._state["calendar"], 0.0, False

    def _tool_get_event(self, event_id: str) -> tuple:
        """Read – returns full details of one event."""
        evt = next(
            (e for e in self._state["calendar"] if e["event_id"] == event_id),
            None,
        )
        if evt is None:
            raise TypeError(f"Event '{event_id}' not found.")
        return evt, 0.0, False

    def _tool_create_event(self, title: str, date: str, time: str,
                            participants: Optional[List[str]] = None,
                            description: str = "") -> tuple:
        """Write – creates a calendar event (no Meet link)."""
        event_id = f"evt_{uuid4().hex[:6]}"
        event = {
            "event_id":     event_id,
            "title":        title,
            "date":         date,
            "time":         time,
            "participants": participants or [],
            "meet_link":    None,
            "description":  description,
        }
        self._state["calendar"].append(event)
        reward = self._partial_reward(0.15, f"create_event_{title}")
        done   = self._check_done()
        return {"event_id": event_id, "title": title}, reward, done

    def _tool_create_meet_event(self, title: str, date: str, time: str,
                                 participants: Optional[List[str]] = None,
                                 description: str = "") -> tuple:
        """Write – creates a calendar event with an auto-generated Meet link.
        Also auto-sends invite emails to all participants."""
        event_id  = f"evt_{uuid4().hex[:6]}"
        meet_link = f"https://meet.google.com/{uuid4().hex[:3]}-{uuid4().hex[:4]}-{uuid4().hex[:3]}"
        event = {
            "event_id":     event_id,
            "title":        title,
            "date":         date,
            "time":         time,
            "participants": participants or [],
            "meet_link":    meet_link,
            "description":  description,
        }
        self._state["calendar"].append(event)

        # Auto-send invite emails to participants
        for email in (participants or []):
            invite = {
                "mail_id": f"mail_{uuid4().hex[:6]}",
                "from":    "teacher@school.edu",
                "to":      email,
                "subject": f"Meeting Invite: {title}",
                "body":    (
                    f"You are invited to '{title}' on {date} at {time}.\n"
                    f"Join via Google Meet: {meet_link}"
                ),
                "date":    "2025-03-13",
                "labels":  [],
            }
            self._state["sent"].append(invite)

        reward = self._partial_reward(0.2, f"create_meet_{title}")
        done   = self._check_done()
        return {"event_id": event_id, "meet_link": meet_link}, reward, done

    # ══════════════════════════════════════════════════════════════════════
    # ── HELPERS ───────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    def _find_mail(self, mail_id: str) -> Dict[str, Any]:
        """Find an email in inbox or sent; raise TypeError if not found."""
        return self.world.find_mail(mail_id)

    def _find_mail_safe(self, mail_id: str) -> Optional[Dict[str, Any]]:
        """Find an email without raising."""
        return self.world.find_mail_safe(mail_id)

    def _get_student_math_grade(self, student_id: str) -> Optional[float]:
        """Return the computed final Math grade for a student, or None."""
        return self.world.get_student_math_grade(student_id)

    def _eval_formula(self, sheet: Dict[str, Any], formula: str) -> Any:
        """
        Evaluate a simple AVERAGE(C#,D#,E#) formula over sheet cells.
        Returns the numeric result or the original formula string if unparseable.
        """
        return self.world.eval_formula(sheet, formula)

    def _audit_action(self, tool: str, params: dict) -> float:
        """
        Returns -0.10 penalty if the action is not required by the task,
        or targets the wrong subject.
        Read-only tools are always free.
        Returns 0.0 if the action is legitimate.
        """
        if tool in READ_TOOLS:
            return 0.0

        task_name = self._task["name"] if self._task else ""
        allowed_map = _build_allowed_actions(self._state)
        allowed = allowed_map.get(task_name, {})

        if tool not in allowed:
            return -0.10

        validator = allowed[tool]
        if not validator(params):
            return -0.10

        return 0.0
    
    def _partial_reward(self, amount: float, key: str) -> float:
        """
        Returns `amount` the first time this key is seen this episode,
        0.0 on subsequent calls (prevents reward hacking by repeating actions).
        """
        if not hasattr(self, "_rewarded") or self._ep_state is None:
            return amount
        full_key = f"{self._ep_state.episode_id}:{key}"
        if full_key in self._rewarded:
            return 0.0
        self._rewarded[full_key] = True
        return amount

    def _check_done(self) -> bool:
        """
        An episode ends when the grader score reaches 1.0.
        We run a lightweight check here so the agent gets a done=True signal.
        """
        return self.grade() >= 0.99

    def grade(self) -> float:
        """
        Run the grader for the active task and return a score in [0.0, 1.0].
        Called externally by the inference script after the episode ends.
        """
        if self._task is None:
            return 0.0
        task_name = self._task["name"]
        result = run_grader(task_name, self._state)
        return result["score"]

    def final_score(self) -> float:
        base = self.grade()
        positive_rewards = sum(r for r in self._rewards if r > 0)
        negative_rewards = sum(r for r in self._rewards if r < 0)
        efficiency_bonus = (positive_rewards * 0.05) + (negative_rewards * 0.3)
        return round(max(0.0, min(1.0, base + efficiency_bonus)), 4)
