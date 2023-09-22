import logging
import sys
import requests
import json
from config import GOOGLE_API_KEY, YOUTUBE_PLAYLIST_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from confluent_kafka import Producer



KSQL_URL = "http://localhost:8088"  # Default KSQL REST API endpoint

# Existing YouTube fetching functions
def fetch_playlist_items_page(google_api_key, youtube_playlist_id, page_token=None):
    response = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
                            params={
                                "key": google_api_key,
                                "playlistId": youtube_playlist_id,
                                "part": "contentDetails",
                                "pageToken": page_token
                            })

    return response.json()

def fetch_videos_page(google_api_key, video_id, page_token=None):
    response = requests.get("https://www.googleapis.com/youtube/v3/videos",
                            params={
                                "key": google_api_key,
                                "id": video_id,
                                "part": "snippet,statistics",
                                "pageToken": page_token
                            })

    return response.json()

# Fetch all videos in a playlist
def fetch_playlist_items(google_api_key, youtube_playlist_id):
    page_token = None
    while True:
        payload = fetch_playlist_items_page(google_api_key, youtube_playlist_id, page_token)
        yield from payload["items"]
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

def fetch_videos(google_api_key, video_id):
    page_token = None
    while True:
        payload = fetch_videos_page(google_api_key, video_id, page_token)
        yield from payload["items"]
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

# Summarize the video data
def summarize_video(video):
    return {
        "video_id": video["id"],
        "title": video["snippet"]["title"],
        "views": int(video["statistics"].get("viewCount", 0)),
        "likes": int(video["statistics"].get("likeCount", 0)),
        "comments": int(video["statistics"].get("commentCount", 0)),
    }

# Send a KSQL command to the KSQL REST API
def send_ksql_command(command):
    headers = {
        "Content-Type": "application/vnd.ksql.v1+json",
        "Accept": "application/vnd.ksql.v1+json",
    }
    payload = {
        "ksql": command,
        "streamsProperties": {}
    }
    response = requests.post(f"{KSQL_URL}/ksql", headers=headers, json=payload)
    return response.json()

def setup_ksql_stream():
    command = """
    CREATE STREAM IF NOT EXISTS youtube_videos_stream (
        video_id VARCHAR PRIMARY KEY,
        title VARCHAR,
        views BIGINT,
        likes BIGINT,
        comments BIGINT
    ) WITH (
        KAFKA_TOPIC='youtube_videos',
        VALUE_FORMAT='JSON',
        KEY='video_id'
    );
    """
    return send_ksql_command(command)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload)


import time

def main():
    logging.info("START")
    producer = Producer({'bootstrap.servers': 'localhost:9092'})

    processed_video_ids = set()  # Set to keep track of processed video IDs

    while True:  # Infinite loop to keep checking for new videos
        for video_item in fetch_playlist_items(GOOGLE_API_KEY, YOUTUBE_PLAYLIST_ID):
            video_id = video_item["contentDetails"]["videoId"]

            # Skip the video if it has already been processed
            if video_id in processed_video_ids:
                continue

            for video in fetch_videos(GOOGLE_API_KEY, video_id):
                summarized_video = summarize_video(video)
                logging.info("GOT %s", summarized_video)

                send_telegram_message(f"New video detected: {summarized_video}")

                producer.produce(
                    topic="youtube_videos",
                    key=video_id,
                    value=json.dumps(summarized_video),
                )

            processed_video_ids.add(video_id)  # Add the video ID to the processed set

        producer.flush()
        setup_ksql_stream()
        time.sleep(1)  # Sleep for 1 second before the next iteration

    # You can then send more KSQL commands to query or transform the data as required

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
