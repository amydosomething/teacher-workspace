"""
tools.py
Tool definitions for the Teacher Workspace Environment.
"""

from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

def _build_tool_registry():
    """
    Builds and returns the tool registry for the Teacher Workspace Environment.
    This is a simplified version of the tool handlers from the original environment.
    """
    
    # Define the tools dictionary with their names, descriptions, and parameters
    tools = {
        # Google Classroom - read
        "list_classrooms": {
            "name": "list_classrooms",
            "description": "Returns all classrooms in the workspace",
            "parameters": {}
        },
        "get_classroom": {
            "name": "get_classroom",
            "description": "Returns full details of a specific classroom",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "string", "description": "ID of the classroom to retrieve"}
                },
                "required": ["class_id"]
            }
        },
        "list_announcements": {
            "name": "list_announcements",
            "description": "Returns announcements for a specific classroom",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "string", "description": "ID of the classroom"}
                },
                "required": ["class_id"]
            }
        },
        
        # Google Classroom - write
        "create_classroom": {
            "name": "create_classroom",
            "description": "Creates a new classroom",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the classroom"},
                    "section": {"type": "string", "description": "Section of the classroom"},
                    "description": {"type": "string", "description": "Optional description of the classroom"}
                },
                "required": ["name", "section"]
            }
        },
        "delete_classroom": {
            "name": "delete_classroom",
            "description": "Deletes a classroom",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "string", "description": "ID of the classroom to delete"}
                },
                "required": ["class_id"]
            }
        },
        "create_announcement": {
            "name": "create_announcement",
            "description": "Posts an announcement to a classroom",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "string", "description": "ID of the classroom"},
                    "text": {"type": "string", "description": "Text of the announcement"}
                },
                "required": ["class_id", "text"]
            }
        },
        "delete_announcement": {
            "name": "delete_announcement",
            "description": "Deletes an announcement",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "string", "description": "ID of the classroom"},
                    "announcement_id": {"type": "string", "description": "ID of the announcement to delete"}
                },
                "required": ["class_id", "announcement_id"]
            }
        },
        "add_comment": {
            "name": "add_comment",
            "description": "Adds a comment to an announcement",
            "parameters": {
                "type": "object",
                "properties": {
                    "announcement_id": {"type": "string", "description": "ID of the announcement"},
                    "text": {"type": "string", "description": "Text of the comment"}
                },
                "required": ["announcement_id", "text"]
            }
        },
        "delete_comment": {
            "name": "delete_comment",
            "description": "Deletes a comment from an announcement",
            "parameters": {
                "type": "object",
                "properties": {
                    "announcement_id": {"type": "string", "description": "ID of the announcement"},
                    "comment_id": {"type": "string", "description": "ID of the comment to delete"}
                },
                "required": ["announcement_id", "comment_id"]
            }
        },
        
        # Google Sheets - read
        "list_sheets": {
            "name": "list_sheets",
            "description": "Returns names of all sheets in the workspace",
            "parameters": {}
        },
        "get_cells": {
            "name": "get_cells",
            "description": "Returns cells from a specific sheet",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet to retrieve"},
                    "cell_range": {"type": "string", "description": "Cell range to retrieve (default: A1:Z100)"}
                },
                "required": ["sheet_name"]
            }
        },
        
        # Google Sheets - write
        "create_sheet": {
            "name": "create_sheet",
            "description": "Creates a new spreadsheet sheet with optional headers",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet to create"},
                    "headers": {"type": "array", "items": {"type": "string"}, "description": "Optional list of header names"}
                },
                "required": ["sheet_name"]
            }
        },
        "delete_sheet": {
            "name": "delete_sheet",
            "description": "Deletes a sheet",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet to delete"}
                },
                "required": ["sheet_name"]
            }
        },
        "update_cell": {
            "name": "update_cell",
            "description": "Sets the value of a single cell",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet"},
                    "cell": {"type": "string", "description": "Cell reference (e.g., A1)"},
                    "value": {"type": "any", "description": "Value to set in the cell"}
                },
                "required": ["sheet_name", "cell", "value"]
            }
        },
        "add_note": {
            "name": "add_note",
            "description": "Adds a text note to a cell",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet"},
                    "cell": {"type": "string", "description": "Cell reference (e.g., A1)"},
                    "note": {"type": "string", "description": "Note text to add"}
                },
                "required": ["sheet_name", "cell", "note"]
            }
        },
        "set_formula": {
            "name": "set_formula",
            "description": "Stores a formula string and computes a numeric result",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet"},
                    "cell": {"type": "string", "description": "Cell reference (e.g., A1)"},
                    "formula": {"type": "string", "description": "Formula to set (supports AVERAGE(C#,D#,E#) format)"}
                },
                "required": ["sheet_name", "cell", "formula"]
            }
        },
        "sort_range": {
            "name": "sort_range",
            "description": "Sorts data rows by a given column",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet"},
                    "column": {"type": "string", "description": "Column to sort by (e.g., F)"},
                    "ascending": {"type": "boolean", "description": "Sort in ascending order (default: False)"}
                },
                "required": ["sheet_name", "column"]
            }
        },
        "filter_range": {
            "name": "filter_range",
            "description": "Returns rows where column matches a condition (read-only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {"type": "string", "description": "Name of the sheet"},
                    "column": {"type": "string", "description": "Column to filter on"},
                    "operator": {"type": "string", "description": "Operator to use (> >= < <= ==)"},
                    "value": {"type": "any", "description": "Value to compare against"}
                },
                "required": ["sheet_name", "column", "operator", "value"]
            }
        },
        
        # Gmail - read
        "list_inbox": {
            "name": "list_inbox",
            "description": "Returns all emails in the inbox (summary view)",
            "parameters": {}
        },
        "read_mail": {
            "name": "read_mail",
            "description": "Returns full content of one email and marks it as read",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to read"}
                },
                "required": ["mail_id"]
            }
        },
        "search_mail": {
            "name": "search_mail",
            "description": "Searches inbox by subject or sender (case-insensitive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        },
        
        # Gmail - write
        "create_draft": {
            "name": "create_draft",
            "description": "Saves an email draft",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"}
                },
                "required": ["to", "subject", "body"]
            }
        },
        "send_mail": {
            "name": "send_mail",
            "description": "Sends an email and adds it to sent box",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"}
                },
                "required": ["to", "subject", "body"]
            }
        },
        "categorise_mail": {
            "name": "categorise_mail",
            "description": "Sets the category field of an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to categorize"},
                    "category": {"type": "string", "description": "Category to assign"}
                },
                "required": ["mail_id", "category"]
            }
        },
        "star_mail": {
            "name": "star_mail",
            "description": "Stars an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to star"}
                },
                "required": ["mail_id"]
            }
        },
        "mark_unread": {
            "name": "mark_unread",
            "description": "Marks an email as unread",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to mark as unread"}
                },
                "required": ["mail_id"]
            }
        },
        "mark_important": {
            "name": "mark_important",
            "description": "Marks an email as important",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to mark as important"}
                },
                "required": ["mail_id"]
            }
        },
        "mark_spam": {
            "name": "mark_spam",
            "description": "Marks an email as spam",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to mark as spam"}
                },
                "required": ["mail_id"]
            }
        },
        "delete_mail": {
            "name": "delete_mail",
            "description": "Deletes an email from inbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to delete"}
                },
                "required": ["mail_id"]
            }
        },
        "create_label": {
            "name": "create_label",
            "description": "Creates a new Gmail label",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the label to create"}
                },
                "required": ["name"]
            }
        },
        "assign_label": {
            "name": "assign_label",
            "description": "Assigns a label to a sent or inbox email",
            "parameters": {
                "type": "object",
                "properties": {
                    "mail_id": {"type": "string", "description": "ID of the email to label"},
                    "label": {"type": "string", "description": "Name of the label to assign"}
                },
                "required": ["mail_id", "label"]
            }
        },
        
        # Calendar / Meet - read
        "list_events": {
            "name": "list_events",
            "description": "Returns all calendar events",
            "parameters": {}
        },
        "get_event": {
            "name": "get_event",
            "description": "Returns full details of one event",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID of the event to retrieve"}
                },
                "required": ["event_id"]
            }
        },
        
        # Calendar / Meet - write
        "create_event": {
            "name": "create_event",
            "description": "Creates a calendar event (no Meet link)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the event"},
                    "date": {"type": "string", "description": "Date of the event (YYYY-MM-DD)"},
                    "time": {"type": "string", "description": "Time of the event (HH:MM)"},
                    "participants": {"type": "array", "items": {"type": "string"}, "description": "List of participant emails"},
                    "description": {"type": "string", "description": "Description of the event"}
                },
                "required": ["title", "date", "time"]
            }
        },
        "create_meet_event": {
            "name": "create_meet_event",
            "description": "Creates a calendar event with an auto-generated Meet link and sends invites",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the event"},
                    "date": {"type": "string", "description": "Date of the event (YYYY-MM-DD)"},
                    "time": {"type": "string", "description": "Time of the event (HH:MM)"},
                    "participants": {"type": "array", "items": {"type": "string"}, "description": "List of participant emails"},
                    "description": {"type": "string", "description": "Description of the event"}
                },
                "required": ["title", "date", "time"]
            }
        }
    }
    
    return tools


# Export the tools as a constant
TOOL_DEFINITIONS = _build_tool_registry()