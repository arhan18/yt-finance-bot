#!/bin/bash
# Fiscalore Video Pipeline - Local Run Script
# Generates a video and optionally uploads to YouTube

set -e

# Default settings
ASPECT="16:9"
VOICE="en-US-GuyNeural"
UPLOAD=false
TOPIC=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --topic)
      TOPIC="$2"
      shift 2
      ;;
    --shorts)
      ASPECT="9:16"
      shift
      ;;
    --upload)
      UPLOAD=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Generate topic if not provided
if [ -z "$TOPIC" ]; then
  TOPICS=(
    "The Psychology of Money"
    "Why Most Investors Fail"
    "The Power of Compound Interest"
    "Hidden Tax on Your Savings"
    "How Inflation Steals Your Wealth"
    "The Secret to Building Wealth"
    "Why Rich Get Richer"
    "Money Myths Exposed"
    "The Future of Finance"
    "How Banks Really Work"
  )
  INDEX=$((RANDOM % ${#TOPICS[@]}))
  TOPIC="${TOPICS[$INDEX]}"
fi

echo "=== Fiscalore Video Pipeline ==="
echo "Topic: $TOPIC"
echo "Format: $ASPECT"
echo ""

# Generate video
echo "Generating video..."
python3 cli.py \
  --video-subject "$TOPIC" \
  --video-language en \
  --video-source pexels \
  --video-aspect "$ASPECT" \
  --voice-name "$VOICE" \
  --subtitle-enabled \
  --video-clip-duration 5 \
  --bgm-type random \
  --bgm-volume 0.15 \
  --video-count 1

# Find generated video
LATEST_VIDEO=$(ls -t ./storage/tasks/*/final-*.mp4 2>/dev/null | head -1)

if [ -z "$LATEST_VIDEO" ]; then
  echo "Error: No video generated"
  exit 1
fi

echo ""
echo "Video generated: $LATEST_VIDEO"

# Upload to YouTube if requested
if [ "$UPLOAD" = true ]; then
  echo ""
  echo "Uploading to YouTube..."
  
  DESCRIPTION="Discover the truth about $TOPIC. 

This video is for educational and entertainment purposes only. Nothing here is financial advice.

#Fiscalore #Finance #Money #Investing #Wealth"
  
  python3 youtube_upload.py \
    "$LATEST_VIDEO" \
    --title "$TOPIC | Fiscalore" \
    --description "$DESCRIPTION" \
    --tags finance money investing wealth fiscalore \
    --privacy public
fi

echo ""
echo "Done!"
