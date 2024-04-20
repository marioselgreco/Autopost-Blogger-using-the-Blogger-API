import csv
import html
import time
import random
import logging
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OAuth 2.0 Setup (Add your CLIENT_ID and CLIENT_SECRET here)
CLIENT_ID = 'add your id'
CLIENT_SECRET = 'add your secret'

FLOW = OAuth2WebServerFlow(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope='https://www.googleapis.com/auth/blogger',
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

# Authenticate and create a service object
storage = Storage('blogger_credentials.dat')
credentials = storage.get()
if credentials is None or credentials.invalid:
    credentials = run_flow(FLOW, storage)
service = build('blogger', 'v3', credentials=credentials)

def create_post(blog_id, title, body, labels=None, search_description=None):
    post_body = {
        'kind': 'blogger#post',
        'blog': {'id': blog_id},
        'title': title,
        'content': body,
    }

    if labels:
        post_body['labels'] = labels.split(', ') # Assuming labels are comma-separated in the CSV

    if search_description:
        # Blogger API does not directly support search description in the API, so we include it as part of the content
        body_with_meta = f'<meta name="description" content="{search_description}"/>\n' + body
        post_body['content'] = body_with_meta

    try:
        request = service.posts().insert(blogId=blog_id, body=post_body, isDraft=False)
        response = request.execute()
        logging.info(f"Post created with ID: {response['id']}")
        return True
    except Exception as e:
        logging.error(f"Error creating post: {e}")
        return False

def parse_html_body(body):
    body = html.unescape(body)
    body = body.replace('<br>', '\n')
    body = '<p>' + body.replace('\n\n', '</p><p>') + '</p>'
    return body

def create_post_with_retry(blog_id, title, body, labels=None, search_description=None, max_retries=3):
    for attempt in range(max_retries):
        if create_post(blog_id, title, body, labels, search_description):
            return True
        else:
            logging.info(f"Retry {attempt + 1} of {max_retries}")
            time.sleep(5)
    return False

def process_blog_from_csv(blog_id, csv_file_path):
    with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            title = row.get('Title', '')
            body = parse_html_body(row.get('Body', ''))
            labels = row.get('Labels', '')
            search_description = row.get('SearchDescription', '')
            if not create_post_with_retry(blog_id, title, body, labels, search_description):
                logging.info("Failed to create post after retries, moving to next.")
            time.sleep(random.randint(30, 180))

def main():
    blog_csv_mappings = [
        {"blog_id": "add your blog id", "csv_file": "add your csv file"},
    ]

    for mapping in blog_csv_mappings:
        process_blog_from_csv(mapping["blog_id"], mapping["csv_file"])

if __name__ == '__main__':
    main()
