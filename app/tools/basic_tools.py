from datetime import datetime


notes = []


def get_time():
    """Return the current local time."""
    return datetime.now().strftime("%I:%M %p")


def save_note(note: str):
    """Save a short note in memory for this running application."""
    notes.append(note)
    return f"I saved this note: {note}"