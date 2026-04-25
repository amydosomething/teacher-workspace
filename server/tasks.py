"""
tasks.py
Task definitions for the Teacher Workspace Environment.
Contains all task information and criteria.
"""

from typing import Dict, List


TASKS = {
    "setup_new_course": {
        "name":   "setup_new_course",
        "prompt": (
            "A new elective course 'Computer Science 101' is starting next week for "
            "Grade 10 Section A. You need to:\n"
            "1. Create a new classroom named 'Computer Science 101' with section "
            "'Grade 10 - Section A'.\n"
            "2. Create a new gradebook sheet called 'CS Gradebook' with headers: "
            "Student Name, Student ID, Assignment 1 (%), Assignment 2 (%), "
            "Final Grade (%), Notes.\n"
            "3. Post a welcome announcement in the new classroom: "
            "'Welcome to Computer Science 101! Please check the gradebook for "
            "upcoming assignments.'\n"
            "Complete all three steps."
        ),
        "difficulty": "easy",
        "expected_tools": ["create_classroom", "create_sheet", "create_announcement"],
        "rubric_criteria": [
            {"name": "created_cs_classroom", "description": "Created 'Computer Science 101' classroom", "check": "tool_used:create_classroom"},
            {"name": "created_cs_gradebook", "description": "Created 'CS Gradebook' sheet", "check": "tool_used:create_sheet"},
            {"name": "posted_welcome_announcement", "description": "Posted welcome announcement", "check": "tool_used:create_announcement"},
        ]
    },

    "grade_and_notify": {
        "name":   "grade_and_notify",
        "prompt": (
            "End-of-week grading duties:\n"
            "1. Calculate the Math final grade for each student as the average of "
            "Midterm (%), Assignment 1 (%), and Assignment 2 (%) and update column F "
            "in 'Math Gradebook' (rows 2-6).\n"
            "   For grade calculations: average = (C + D + E) / 3, computed precisely. "
            "   Example: (55 + 60 + 58) / 3 = 57.67. Do NOT round to nearest whole number.\n"
            "2. In the 'Math Gradebook', find the student whose final grade is below 60. "
            "   Add a note to column G of that student's row: 'Recommended for tutoring'.\n"
            "   (Look up which row that student is in based on their computed final grade.)\n"
            "3. Send an individual email to each student with their Math final grade.\n"
            "   Subject: 'Your Math 101 Final Grade'\n"
            "   Body: 'Hi <name>, your final Math grade is <grade>%. Keep it up!'\n"
            "4. Star the email from Mrs. Martinez — it needs follow-up.\n"
            "Complete all steps."
        ),
        "difficulty": "medium",
        "expected_tools": ["set_formula", "add_note", "send_mail", "star_mail"],
        "rubric_criteria": [
            {"name": "calculated_final_grades", "description": "Calculated final grades in Math Gradebook", "check": "tool_used:set_formula"},
            {"name": "added_tutoring_note", "description": "Added note to failing student", "check": "tool_used:add_note"},
            {"name": "emailed_all_students", "description": "Sent emails to all students", "check": "tool_used:send_mail"},
            {"name": "starred_martinez_email", "description": "Starred Mrs. Martinez email", "check": "tool_used:star_mail"},
        ]
    },

    "end_of_semester": {
        "name":   "end_of_semester",
        "prompt": (
            "End-of-semester admin tasks:\n"
            "1. In 'Math Gradebook', set a formula in F2 to calculate Alice's final "
            "grade as AVERAGE(C2,D2,E2). Do the same for rows 3-6 for all students.\n"
            "2. Sort the 'Math Gradebook' by column F (Final Grade) in descending order.\n"
            "3. Create a Gmail label called 'End of Semester'.\n"
            "4. Send a grade report email to each student's parent with subject "
            "'End of Semester Report' and body: "
            "'Dear <parent_name>, your child <student_name> has completed the semester. "
            "Please contact us to discuss their progress.'\n"
            "5. Assign the label 'End of Semester' to all parent emails you just sent.\n"
            "6. Schedule a parent-teacher meeting for each failing student that is the student whose final grade is less than 60 in the gradebook"
            "as a Google Meet event titled 'Parent Meeting - <student_name>' on "
            "2025-04-20 at 14:00, inviting the parent's email.\n"
            "Complete all steps."
        ),
        "difficulty": "hard",
        "expected_tools": ["set_formula", "sort_range", "create_label", "send_mail", "assign_label", "create_meet_event"],
        "rubric_criteria": [
            {"name": "set_formulas", "description": "Set formulas in Math Gradebook", "check": "tool_used:set_formula"},
            {"name": "sorted_gradebook", "description": "Sorted gradebook by final grade", "check": "tool_used:sort_range"},
            {"name": "created_semester_label", "description": "Created 'End of Semester' label", "check": "tool_used:create_label"},
            {"name": "emailed_parents", "description": "Sent emails to all parents", "check": "tool_used:send_mail"},
            {"name": "applied_semester_label", "description": "Applied 'End of Semester' label", "check": "tool_used:assign_label"},
            {"name": "scheduled_meetings", "description": "Scheduled meetings for failing students", "check": "tool_used:create_meet_event"},
        ]
    },
}


def get_task(task_name: str) -> Dict[str, any]:
    """
    Get a task by name.
    
    Args:
        task_name: Name of the task to retrieve
        
    Returns:
        Dictionary containing task information
    """
    return TASKS.get(task_name, TASKS["setup_new_course"])


def get_all_tasks() -> List[Dict[str, any]]:
    """
    Get all tasks.
    
    Returns:
        List of all tasks
    """
    return list(TASKS.values())


def get_task_names() -> List[str]:
    """
    Get all task names.
    
    Returns:
        List of all task names
    """
    return list(TASKS.keys())