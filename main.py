import os
import subprocess
import time
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
AUDIO_PATH = "input_song.mp3"
OUTPUT_DIR = "output/input_song"

user_choices = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a song (MP3/WAV).\nI'll split it into 4 stems and let you choose which to mix back!"
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio or update.message.document
    if not audio:
        return await update.message.reply_text("⚠️ Please send an MP3 or WAV file.")
    
    file = await audio.get_file()
    original_name = getattr(audio, "file_name", "song.mp3")
    await file.download_to_drive(AUDIO_PATH)

    user_id = update.message.from_user.id
    user_choices[user_id] = {"selected": [], "original_name": original_name}

    # Start splitting
    await update.message.reply_text("🎶 Splitting into 4 stems... Please wait!")
    start_time = time.time()

    process = subprocess.Popen(
        f"spleeter separate -p spleeter:4stems -o output {AUDIO_PATH}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # Fake progress updates
    for pct in [25, 50, 75, 100]:
        elapsed = int(time.time() - start_time)
        await update.message.reply_text(f"Progress: {pct}% ⏱ {elapsed}s elapsed")
        time.sleep(3)

    process.wait()
    await update.message.reply_text("✅ Splitting complete! Now choose stems to mix:")

    # Show buttons
    keyboard = [
        [InlineKeyboardButton("🎤 Vocals", callback_data="vocals")],
        [InlineKeyboardButton("🥁 Drums", callback_data="drums")],
        [InlineKeyboardButton("🎸 Bass", callback_data="bass")],
        [InlineKeyboardButton("🎼 Other", callback_data="other")],
        [InlineKeyboardButton("✅ Mix Now", callback_data="done")]
    ]
    await update.message.reply_text(
        "Select stems:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_choices:
        return await query.edit_message_text("⚠️ No song uploaded yet!")

    choice = query.data
    if choice == "done":
        selected = user_choices[user_id]["selected"]
        if not selected:
            return await query.edit_message_text("⚠️ Please select at least one stem!")

        await query.edit_message_text("🎚 Mixing selected stems...")
        await mix_stems(query, user_id, selected)
        return

    if choice not in user_choices[user_id]["selected"]:
        user_choices[user_id]["selected"].append(choice)

    await query.edit_message_text(
        f"✅ Selected so far: {', '.join(user_choices[user_id]['selected'])}\n"
        "Click more or press ✅ Mix Now.",
        reply_markup=query.message.reply_markup
    )

async def mix_stems(query, user_id, selected_stems):
    original_name = user_choices[user_id]["original_name"]
    base_name = os.path.splitext(original_name)[0]
    final_file = f"{base_name}_mixed.mp3"

    stem_files = [f"{OUTPUT_DIR}/{stem}.wav" for stem in selected_stems if os.path.exists(f"{OUTPUT_DIR}/{stem}.wav")]

    if not stem_files:
        return await query.message.reply_text("⚠️ Error: Stems not found!")

    # Mix stems
    inputs = ""
    filters = []
    for i, stem in enumerate(stem_files):
        inputs += f"-i {stem} "
        filters.append(f"[{i}:a]")

    filter_complex = "".join(filters) + f"amix=inputs={len(stem_files)}:duration=longest[aout]"
    subprocess.run(f"ffmpeg {inputs} -filter_complex \"{filter_complex}\" -map \"[aout]\" -y {final_file}", shell=True)

    await query.message.reply_document(
        InputFile(final_file),
        caption=f"✅ Here is your mixed track ({', '.join(selected_stems)})"
    )

    # Cleanup everything
    shutil.rmtree("output", ignore_errors=True)
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)
    if os.path.exists(final_file):
        os.remove(final_file)
    user_choices.pop(user_id, None)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.MP3 | filters.Document.WAV, handle_audio))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
