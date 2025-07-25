import logging
import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Bot token
BOT_TOKEN = '8432631858:AAGO7i91jJ0K8Q4n_dfrr6b8q5xhbSXarg0'

# Initialize logging with a higher level to reduce output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Change level to WARNING to reduce logs
)

# Dictionary to store user IDs and their corresponding anonymous IDs
user_data = {}

# Function to generate a unique anonymous ID for each user
def generate_anonymous_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        anon_id = generate_anonymous_id()
        user_data[user_id] = {'anon_id': anon_id}
        await update.message.reply_text(f"Welcome! Your anonymous ID is {anon_id}. You can now send messages anonymously.")
    else:
        anon_id = user_data[user_id]['anon_id']
        await update.message.reply_text(f"Welcome back! Your anonymous ID is {anon_id}.")

# Function to handle all messages and media
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Assign an anonymous ID if the user doesn't have one
    if user_id not in user_data:
        anon_id = generate_anonymous_id()
        user_data[user_id] = {'anon_id': anon_id}
    else:
        anon_id = user_data[user_id]['anon_id']

    # Handling text and media messages
    if update.message.text:
        # Prepare the message with bold formatting for the anonymous ID
        message = f"*{anon_id}*: {update.message.text}"  # Format text with the anonymous ID in bold
        await broadcast_message(message, user_id, context)  # Broadcast the message
    elif update.message.photo:
        content = update.message.photo[-1].file_id  # Get the file ID of the last photo
        await broadcast_media(content, user_id, context, 'photo')  # Broadcast the media
    elif update.message.sticker:
        content = update.message.sticker.file_id  # Get the file ID of the sticker
        await broadcast_media(content, user_id, context, 'sticker')  # Broadcast the media
    elif update.message.video:
        content = update.message.video.file_id  # Get the file ID of the video
        await broadcast_media(content, user_id, context, 'video')  # Broadcast the media
    elif update.message.voice:
        content = update.message.voice.file_id  # Get the file ID of the voice note
        await broadcast_media(content, user_id, context, 'voice')  # Broadcast the media

# Function to broadcast text messages to all users
async def broadcast_message(content, sender_id, context):
    for user_id in user_data.keys():
        if user_id != sender_id:  # Avoid sending the message back to the sender
            try:
                # Sending formatted text with sender's anonymous ID in bold
                await context.bot.send_message(chat_id=user_id, text=content, parse_mode='MarkdownV2')  # Use MarkdownV2
            except Exception as e:
                logging.warning(f"Failed to send message to {user_id}: {e}")

# Function to broadcast media to all users
async def broadcast_media(content, sender_id, context, media_type):
    for user_id in user_data.keys():
        if user_id != sender_id:  # Avoid sending the message back to the sender
            try:
                # Sending the actual media (sticker/photo/video/voice)
                if media_type == 'sticker':
                    await context.bot.send_sticker(chat_id=user_id, sticker=content)  # Sends stickers
                elif media_type == 'photo':
                    await context.bot.send_photo(chat_id=user_id, photo=content)  # Sends photos
                elif media_type == 'video':
                    await context.bot.send_video(chat_id=user_id, video=content)  # Sends videos
                elif media_type == 'voice':
                    await context.bot.send_voice(chat_id=user_id, voice=content)  # Sends voice notes
            except Exception as e:
                logging.warning(f"Failed to send media to {user_id}: {e}")

# Command to retrieve stored messages
async def retrieve_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_data:
        await update.message.reply_text("You haven't sent any messages yet.")
    else:
        messages = user_data[user_id].get('messages', [])
        if messages:
            await update.message.reply_text("Here are your stored messages:\n" + "\n".join(messages))
        else:
            await update.message.reply_text("No messages found.")

# Command to send a message to another user
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if the user has provided a target user ID and a message
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /send <target_user_id> <message>")
        return

    target_user_id = context.args[0]  # The target user ID
    message_content = ' '.join(context.args[1:])  # The message to send

    # Store the message in the target user's data
    if target_user_id in user_data:
        user_data[target_user_id].setdefault('messages', []).append(f"From *{user_data[user_id]['anon_id']}*: {message_content}")  # Store with bold formatting
        await update.message.reply_text(f"Message sent to user {target_user_id}.")
    else:
        await update.message.reply_text(f"User {target_user_id} not found.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("retrieve", retrieve_messages))
    application.add_handler(CommandHandler("send", send_message))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Run the bot and keep it running silently in the background
    application.run_polling()

if __name__ == '__main__':
    main()
