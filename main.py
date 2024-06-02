import os.path
import base64

from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from openai import OpenAI

from dotenv import load_dotenv
import os


load_dotenv()

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

TAGS = ['marketing', 'personal', 'work', 'job applications', 'travel', 'newsletter', 'finances', 'receipts']
MAX_RESULTS = 10

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def decode_base64url(base64url):
    missing_padding = len(base64url) % 4
    if missing_padding:
        base64url += '=' * (4 - missing_padding)
    return base64.urlsafe_b64decode(base64url).decode('utf-8')

def fetch_emails(service):
    results = service.users().messages().list(userId='me', maxResults=MAX_RESULTS).execute()
    messages = results.get('messages', [])

    emails = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
        msg_str = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
        mime_msg = message_from_bytes(msg_str)

        payload = get_message_payload(mime_msg)
        if payload is None:
            continue  # Skip emails that cannot be processed

        emails.append({
            'id': message['id'],
            'snippet': payload
        })

    return emails

def get_message_payload(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain' or content_type == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode()

    return None

def categorize_email(email_content):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Categorize the following email content into one of these tags:{tags}. Only return the tag, nothing else. If it doesn't fit any, return 'none':\n\n{email_content}"}
            ],
        max_tokens=100
    )
    category = completion.choices[0].message.content
    return category if category in TAGS else 'none'

def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_id = next((label['id'] for label in labels if label['name'].lower() == label_name.lower()), None)
    
    if not label_id:
        label = {
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
            'name': label_name
        }
        new_label = service.users().labels().create(userId='me', body=label).execute()
        label_id = new_label['id']
    
    return label_id

def apply_label_to_email(service, email_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={'addLabelIds': [label_id]}
    ).execute()

def main():
    service = authenticate_gmail()
    emails = fetch_emails(service)
    
    for email in emails:
        category = categorize_email(email['snippet'])
        if category != 'none':
            label_id = get_or_create_label(service, category)
            apply_label_to_email(service, email['id'], label_id)
    
    print("Emails fetched, categorized, and labeled in Gmail.")

if __name__ == '__main__':
    main()