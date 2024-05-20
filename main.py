import requests
import json
import re
from telegram import ParseMode, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# Path to the JSON file
JSON_FILE = 'user_data.json'
site_url = 'vipurl.in'

# Replace 'YOUR_CHANNEL_ID' with the ID of your channel
CHANNEL_ID = '-1002135471172'

# Function to load user data from JSON file
def load_user_data():
    try:
        with open(JSON_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to save user data to JSON file
def save_user_data(data):
    with open(JSON_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def load_chat_ids():
    chat_ids = []
    try:
        with open('chat_ids.json', 'r') as file:
            try:
                existing_data = json.load(file)
                chat_ids = [entry['chat_id'] for entry in existing_data]
            except json.JSONDecodeError:
                # Handle case where the file is empty or not valid JSON
                pass
    except FileNotFoundError:
        # Handle case where the file doesn't exist
        pass
    return chat_ids

# Define a function to load admin IDs from admins.json file
def load_admin_ids():
    admin_ids = []
    try:
        with open('admins.json', 'r') as file:
            admins_data = json.load(file)
            admin_ids = admins_data.get('admins', [])
    except FileNotFoundError:
        pass
    return admin_ids

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    name = user.first_name
    username = user.username if user.username else 'NA'
    chat_id = update.effective_chat.id

    # Check if chat ID already exists in the JSON file
    if not is_chat_id_exists(chat_id):
        # Append chat ID if it doesn't already exist
        append_chat_id(chat_id)
    
    # Load existing user data
    user_data = load_user_data()
    
    # Send user details to the channel
    user_details = (
        f"User Details:\n"
        f"First Name: {user.first_name}\n"
        f"Last Name: {user.last_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: {user.id}"
    )
    context.bot.send_message(chat_id=CHANNEL_ID, text=user_details)
    
    # Check if user already exists
    for user_info in user_data:
        if user_info['user_id'] == user_id:
            if user_info['api_key'] is None:
                update.message.reply_text("Hey, send me your API key 🔑 so you can log in. You can get it at https://vipurl.in/member/tools/api.")
                return
            else:
                update.message.reply_text(
                    "<b>Welcome back!</b> You can send any link to shorten or forward a message. 🌐 💌",
                    parse_mode=ParseMode.HTML
                )
                return
    
    # If user doesn't exist, add them to the user data
    user_info = {
        'user_id': user_id,
        'name': name,
        'username': username,
        'api_key': None,  # Initialize API key as None
    }
    user_data.append(user_info)
    
    # Save updated user data
    save_user_data(user_data)
    
     
    # Send a welcome message to the user
    update.message.reply_text(f'Hey, send me your API key 🔑 so you can log in. You can get it at https://vipurl.in/member/tools/api.')

# Function to handle the /shortlinkapi command
def set_api(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        api_key = context.args[0]
    except IndexError:
        update.message.reply_text("Usage: /api <API_KEY>")
        return
    
    # Load existing user data
    user_data = load_user_data()
    
    # Check if the provided API key is valid
    if not check_api(api_key):
        update.message.reply_text(f"Invalid API key. Please provide a valid API key \n 🔑 Get it from here: https://vipurl.in/member/tools/api 🌐")
        return
    
    # Find the user and update their API key and site URL
    for user_info in user_data:
        if user_info['user_id'] == user_id:
            user_info['api_key'] = api_key
            save_user_data(user_data)
            update.message.reply_text("The API key has been successfully saved. 🎉👍")
            return
    
    update.message.reply_text("User not found. Please start with the /start command. 🤖")

# Define a function to append chat ID to chat_ids.json
def append_chat_id(chat_id):
    try:
        with open('chat_ids.json', 'r') as file:
            existing_chat_ids = json.load(file)
    except FileNotFoundError:
        existing_chat_ids = []

    # Check if chat ID already exists
    if not any(entry['chat_id'] == chat_id for entry in existing_chat_ids):
        existing_chat_ids.append({"chat_id": chat_id})

        # Write updated data back to the file
        with open('chat_ids.json', 'w') as file:
            json.dump(existing_chat_ids, file, indent=4)

# Define a function to check if chat ID exists in chat_ids.json
def is_chat_id_exists(chat_id):
    try:
        with open('chat_ids.json', 'r') as file:
            existing_chat_ids = json.load(file)
            return any(entry['chat_id'] == chat_id for entry in existing_chat_ids)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# Function to obtain the shortened version of a link
def short_link(update: Update, context: CallbackContext, long_url: str) -> str:
    user_id = update.effective_user.id
    
    # Load existing user data
    user_data = load_user_data()
    
    # Find user's API key
    api_key = None
    for user_info in user_data:
        if user_info['user_id'] == user_id:
            api_key = user_info['api_key']
            break
    
    # Check if API key is set
    if api_key is None:
        update.message.reply_text("Hey, send me your API key 🔑 so you can log in. You can get it at https://vipurl.in/member/tools/api.")
        return None
    
    # Make request to API endpoint to shorten the link
    url = f"https://{site_url}/api?api={api_key}&url={long_url}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        shortened_url = data.get('shortenedUrl')
        if shortened_url:
            return shortened_url
        else:
            update.message.reply_text("Shortened URL not found in the API's response. 😱")
            return None
    else:
        update.message.reply_text("Can't shorten link right now 😱. Please try again later.")
        return None

# Function to check if API key is valid
def check_api(api_key: str) -> bool:
    url = f"https://{site_url}/api?api={api_key}&url=https://webepex.com"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            return True
        else:
            return False
    else:
        return False

# Function to handle messages after /start
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Load existing user data
    user_data = load_user_data()
    
    # Find the user in the user data
    for user_info in user_data:
        if user_info['user_id'] == user_id:
            if user_info['api_key'] is None:
                # Check if the message contains a link
                if re.search(r'http[s]?://\S+', message_text):
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid API. Please send your API key.")
                else:
                    # Check if the provided API key is valid
                    if not check_api(message_text):
                        update.message.reply_text(f"Invalid API key. Please provide a valid API key. \n 🔑 Get it from here: https://vipurl.in/member/tools/api 🌐")
                        return
                    
                    # If API key is null and the message doesn't contain a link, store the received message as API key
                    user_info['api_key'] = message_text
                    save_user_data(user_data)
                    context.bot.send_message(chat_id=update.effective_chat.id, text="The API key has been successfully saved. 🎉👍")
            else:
                # Find all URLs in the message
                urls = re.findall(r'http[s]?://\S+', message_text)
                
                if urls:
                    if len(urls) == 1:
                        # Shorten the single URL and provide a custom response
                        original_url = urls[0]
                        shortened_url = short_link(update, context, original_url)
                        if shortened_url:
                            response_message = (
                                "✨ ✨ Congratulations! Your URL has been successfully shortened! 🚀\n\n"
                                f"🔗 Original URL:\n{original_url}\n\n"
                                f"🌐 Shortened URL:\n<code>{shortened_url}</code>"
                            )
                            context.bot.send_message(
                                chat_id=update.effective_chat.id, 
                                text=response_message, 
                                parse_mode=ParseMode.HTML
                            )
                        else:
                            context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to shorten the link. Please try again later.")
                    else:
                        # Shorten each URL and replace it in the message
                        for url in urls:
                            shortened_url = short_link(update, context, url)
                            if shortened_url:
                                message_text = message_text.replace(url, shortened_url)

                        # Send the modified message back to the user
                        context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
                else:
                    # If no URLs are found, send a different response
                    context.bot.send_message(chat_id=update.effective_chat.id, text="No links were found in your message. 🔎")
            return
    
    # If the user is not found in the user data, ask them to start with /start
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please start with the /start command. 🤖")

# Function to handle forwarded messages containing links
def handle_forwarded_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message = update.message
    
    # Check if the message is forwarded
    if message.forward_from_chat or message.forward_from:
        # Retrieve text from both the message and caption if available
        forwarded_message = message.text or message.caption
        if forwarded_message:
            # Revised regular expression pattern for improved link detection
            links = re.findall(r'http[s]?://\S+', forwarded_message)
            if links:
                for link in links:
                    if "t.me" not in link:  # Skip telegram links
                        # Get the shortened link
                        shortened_link = short_link(update, context, link)
                        if shortened_link:
                            # Replace original link with shortened link
                            forwarded_message = forwarded_message.replace(link, shortened_link)
            # Check if the message has a comment
            if message.caption:
                # Extract links from the comment
                comment_links = re.findall(r'http[s]?://\S+', message.caption)
                if comment_links:
                    for link in comment_links:
                        if "t.me" not in link:  # Skip telegram links
                            # Get the shortened link
                            shortened_link = short_link(update, context, link)
                            if shortened_link:
                                # Replace original link with shortened link in the comment
                                message.caption = message.caption.replace(link, shortened_link)
            # Send the modified message back to the user
            update.message.reply_text(forwarded_message, parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text("The forwarded message does not contain any text.")
    else:
        update.message.reply_text("The message is not forwarded from any chat.")

# Function to handle forwarded messages with images containing links
def handle_forwarded_image_message(update: Update, context: CallbackContext):
    message = update.message
    
    # Check if the message has a caption
    if message.caption:
        # Retrieve the caption
        caption = message.caption
        
        # Revised regular expression pattern for improved link detection
        links = re.findall(r'http[s]?://\S+', caption)
        if links:
            for link in links:
                if "t.me" not in link:  # Skip telegram links
                    # Get the shortened link
                    shortened_link = short_link(update, context, link)
                    if shortened_link:
                        # Replace original link with shortened link in the caption
                        caption = caption.replace(link, shortened_link)
        
        # Send the modified message back to the user
        update.message.reply_photo(message.photo[-1], caption=caption, parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("The forwarded message does not contain any caption.")

# Define a function to handle the /broadcast command
def broadcast(update, context):
    # Get the user ID of the user who sent the command
    user_id = update.effective_user.id

    # Load admin IDs from admins.json file
    admin_ids = load_admin_ids()

    # Check if the user is an admin
    if user_id not in admin_ids:
        update.message.reply_text("You need to be admin to do this.")
        return

    # Get the message to be broadcasted
    if not context.args:
        update.message.reply_text("Please provide a message to broadcast.")
        return
    
    message = ' '.join(context.args)
    
    # Load chat IDs from chat_ids.json file
    chat_ids = load_chat_ids()

    # Broadcast message to all users
    for chat_id in chat_ids:
        context.bot.send_message(chat_id=chat_id, text=message)

def main():
    # Initialize the bot with the correct token
    updater = Updater("6821739116:AAFoaDEuqB_0ro8yynw0cS7heKAl03-Mtxo", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))

    # Register message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Register handler for forwarded messages containing links
    dp.add_handler(MessageHandler(Filters.forwarded & Filters.text, handle_forwarded_message))
    
    # Register handler for forwarded messages containing links
    dp.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_image_message))

    dp.add_handler(CommandHandler("api", set_api))
    
    # Register handler for the /broadcast command
    dp.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
