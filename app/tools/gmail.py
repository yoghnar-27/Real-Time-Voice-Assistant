import base64
import os
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
PENDING_EMAIL = None


def request_email(recipient: str, message: str, subject: str = "Message from your voice assistant"):
    """Store an email draft and ask the user to confirm before sending."""
    global PENDING_EMAIL
    PENDING_EMAIL = {
        "recipient": recipient,
        "subject": subject,
        "message": message,
    }
    return f"Do you want me to send this email to {recipient}?"


def has_pending_email() -> bool:
    return PENDING_EMAIL is not None


def pending_email_confirmation() -> str:
    """Return the confirmation question for the stored email draft."""
    if PENDING_EMAIL is None:
        return "There is no email waiting for confirmation."
    return f"Do you want me to send this email to {PENDING_EMAIL['recipient']}?"


def is_confirmation(text: str) -> bool:
    return text.strip().lower() in {
        "yes",
        "yes send it",
        "send it",
        "confirm",
        "please send it",
    }


def send_pending_email() -> str:
    """Send the confirmed email through Gmail OAuth."""
    global PENDING_EMAIL
    if PENDING_EMAIL is None:
        return "There is no email waiting for confirmation."

    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
    credentials = None

    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise RuntimeError(
                    f"Missing Gmail OAuth file: {credentials_file}. "
                    "Download a Google Desktop OAuth client file first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            credentials = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(credentials.to_json())

    email = EmailMessage()
    email["To"] = PENDING_EMAIL["recipient"]
    email["Subject"] = PENDING_EMAIL["subject"]
    email.set_content(PENDING_EMAIL["message"])
    encoded_message = base64.urlsafe_b64encode(email.as_bytes()).decode()

    service = build("gmail", "v1", credentials=credentials)
    service.users().messages().send(
        userId="me",
        body={"raw": encoded_message},
    ).execute()

    recipient = PENDING_EMAIL["recipient"]
    PENDING_EMAIL = None
    return f"The email was sent to {recipient}."