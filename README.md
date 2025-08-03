# Telegram Audio Stem Splitter Bot 🎶

This Telegram bot lets users upload a song, splits it into 4 stems (Vocals, Drums, Bass, Other), 
allows selection, mixes the chosen stems back into one MP3 with the original filename, 
shows progress updates, and clears storage after completion.

## Features
- Upload MP3/WAV
- Split into Vocals, Drums, Bass, Other
- Progress updates: 25%, 50%, 75%, 100% + elapsed time
- Choose stems via Telegram buttons
- Mix selected stems into final MP3
- Send back with original filename
- Auto cleanup after each task

## 🚀 Deployment on Railway
1. Upload this repo to GitHub
2. Go to [Railway](https://railway.app)
3. Create a New Project → Deploy from GitHub
4. Add Environment Variable:
   - `BOT_TOKEN = Your Telegram Bot Token`
5. Deploy ✅

