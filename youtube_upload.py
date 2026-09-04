#!/usr/bin/env python3
"""
YouTube Upload Script for Fiscalore Channel
Uses OAuth2 credentials to upload videos to YouTube.
Environment variables: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# YouTube API settings
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

# Default settings
DEFAULT_PRIVACY_STATUS = "public"
DEFAULT_CATEGORY_ID = "22"  # People & Blogs
MAX_RETRIES = 3


def get_youtube_service(client_id=None, client_secret=None, refresh_token=None):
    """Build YouTube API service with OAuth2 credentials."""
    
    # Use provided credentials or environment variables
    if not client_id:
        client_id = os.getenv('YOUTUBE_CLIENT_ID')
    if not client_secret:
        client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    if not refresh_token:
        refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing YouTube OAuth credentials. Set environment variables:\n"
            "  YOUTUBE_CLIENT_ID\n"
            "  YOUTUBE_CLIENT_SECRET\n"
            "  YOUTUBE_REFRESH_TOKEN"
        )
    
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[YOUTUBE_UPLOAD_SCOPE]
    )
    
    # Refresh the token
    credentials.refresh(Request())
    
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def upload_video(youtube, video_file, title, description, tags=None, 
                 category_id=DEFAULT_CATEGORY_ID, privacy_status=DEFAULT_PRIVACY_STATUS,
                 thumbnail_path=None):
    """Upload a video to YouTube."""
    
    if tags is None:
        tags = []
    
    body = {
        'snippet': {
            'title': title[:100],  # YouTube max 100 chars
            'description': description[:5000],  # YouTube max 5000 chars
            'tags': tags[:30],  # YouTube max 30 tags
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    retry = 0
    
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  Uploaded {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status == 404:
                retry += 1
                if retry > MAX_RETRIES:
                    raise
                print(f"  Retrying upload (attempt {retry}/{MAX_RETRIES})...")
                time.sleep(2 ** retry)
            else:
                raise
    
    video_id = response['id']
    print(f"  Video uploaded: https://youtube.com/watch?v={video_id}")
    
    # Upload thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            ).execute()
            print(f"  Thumbnail uploaded")
        except Exception as e:
            print(f"  Warning: Failed to upload thumbnail: {e}")
    
    return video_id


def main():
    parser = argparse.ArgumentParser(description='Upload video to YouTube (Fiscalore channel)')
    parser.add_argument('video_file', help='Path to video file')
    parser.add_argument('--title', required=True, help='Video title (max 100 chars)')
    parser.add_argument('--description', required=True, help='Video description')
    parser.add_argument('--tags', nargs='+', default=[], help='Video tags')
    parser.add_argument('--thumbnail', help='Path to thumbnail image (JPG)')
    parser.add_argument('--privacy', default=DEFAULT_PRIVACY_STATUS, 
                       choices=['public', 'unlisted', 'private'],
                       help='Privacy status (default: public)')
    parser.add_argument('--category', default=DEFAULT_CATEGORY_ID, help='Category ID (default: 22)')
    
    args = parser.parse_args()
    
    # Validate video file
    if not os.path.exists(args.video_file):
        print(f"Error: Video file not found: {args.video_file}")
        sys.exit(1)
    
    print(f"Uploading to YouTube (Fiscalore channel)...")
    print(f"  Video: {args.video_file}")
    print(f"  Title: {args.title}")
    print(f"  Privacy: {args.privacy}")
    
    try:
        youtube = get_youtube_service()
        video_id = upload_video(
            youtube,
            args.video_file,
            args.title,
            args.description,
            args.tags,
            args.category,
            args.privacy,
            args.thumbnail
        )
        print(f"\nSuccess! Video ID: {video_id}")
        return 0
    except Exception as e:
        print(f"\nError uploading video: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
