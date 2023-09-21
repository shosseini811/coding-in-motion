import logging
import sys
import requests
import json
from config import config
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

def summarize_video(video):
    return {
        "video_id": video["id"],
        "title": video["snippet"]["title"],
        "views": int(video["statistics"].get("viewCount", 0)),
        "likes": int(video["statistics"].get("likeCount", 0)),
        "comments": int(video["statistics"].get("commentCount", 0)),
    }

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

def main():
    logging.info("START")

    kafka_config = config["kafka"]
    producer = Producer(kafka_config)

    google_api_key = config["google_api_key"]
    youtube_playlist_id = config["youtube_playlist_id"]

    for video_item in fetch_playlist_items(google_api_key, youtube_playlist_id):
        video_id = video_item["contentDetails"]["videoId"]
        for video in fetch_videos(google_api_key, video_id):
            summarized_video = summarize_video(video)
            logging.info("GOT %s", summarized_video)

            def delivery_report(err, msg):
                """ Called once for each message produced to indicate delivery result. """
                if err is not None:
                    logging.error('Message delivery failed: {}'.format(err))
                else:
                    logging.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

            # Send data to Kafka
            producer.produce(
                topic="youtube_videos",
                key=video_id,
                value=json.dumps(summarized_video),
            )

    producer.flush()

    # After producing data to Kafka, set up KSQL stream
    setup_ksql_stream()

    # You can then send more KSQL commands to query or transform the data as required

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
