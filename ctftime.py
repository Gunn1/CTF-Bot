import requests
import time
from datetime import datetime

def get_upcoming_ctf_events(limit=10):
    current_time = int(time.time())
    api_url = f"https://ctftime.org/api/v1/events/?limit={limit}&start={current_time}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        events = response.json()
        return events
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def display_events(events):
    if not events:
        print("No upcoming events found.")
        return
    print(events)
    for event in events:
        title = event.get('title', 'N/A')
        start = event.get('start', 'N/A')
        finish = event.get('finish', 'N/A')
        url = event.get('url', 'N/A')

        if start != 'N/A':
            start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
            start = start.strftime("%Y-%m-%d %H:%M:%S %Z")
        if finish != 'N/A':
            finish = datetime.strptime(finish, "%Y-%m-%dT%H:%M:%S%z")
            finish = finish.strftime("%Y-%m-%d %H:%M:%S %Z")

        print(f"Title: {title}")
        print(f"Start: {start}")
        print(f"Finish: {finish}")
        print(f"URL: {url}")
        print("-" * 40)

if __name__ == "__main__":
    upcoming_events = get_upcoming_ctf_events(limit=10)
    display_events(upcoming_events)
