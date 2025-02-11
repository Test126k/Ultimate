import json
import asyncio
import os
from telethon import TelegramClient, errors

# Configurations
SOURCE_CHANNEL = "https://t.me/your_source_channel"
DEST_CHANNEL = "https://t.me/your_destination_channel"
BATCH_SIZE = 50  # Ek batch me kitne messages fetch karne hain
ACCOUNTS_FILE = "accounts.json"

# Load multiple accounts
def load_accounts():
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

accounts = load_accounts()
clients = []

# Initialize clients
for acc in accounts:
    client = TelegramClient(acc["session"], acc["api_id"], acc["api_hash"])
    clients.append(client)

async def download_and_send(client, message):
    """Media download & send with retries."""
    try:
        file_path = await client.download_media(message, file=f"./downloads/{message.id}")
        if file_path:
            await client.send_file(DEST_CHANNEL, file_path, caption=message.text or "")
            os.remove(file_path)  # Space clear
            return True
    except errors.FloodWaitError as e:
        print(f"FloodWait: {e.seconds}s, waiting...")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"Error: {e}")
    return False

async def forward_messages(client):
    """Messages ko optimized way me forward karega."""
    try:
        print(f"🔄 Connecting {client.session.filename}...")
        await client.connect()
        source = await client.get_entity(SOURCE_CHANNEL)
        messages = await client.get_messages(source, limit=BATCH_SIZE)

        tasks = []
        for msg in messages:
            if msg.media:
                tasks.append(download_and_send(client, msg))

        await asyncio.gather(*tasks)
        print(f"✅ {client.session.filename} completed!")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    tasks = [forward_messages(client) for client in clients]
    await asyncio.gather(*tasks)

with clients[0]:  # First client se loop start
    clients[0].loop.run_until_complete(main())
