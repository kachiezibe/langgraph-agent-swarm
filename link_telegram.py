import os
import sys
import requests
import json

# Your Bot Token - Loaded securely from environment variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

def update_env(chat_id):
    env_path = ".env"
    if not os.path.exists(env_path):
        print("⚠️ .env file not found!")
        return False
        
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    has_token = False
    has_chat_id = False
    
    for line in lines:
        if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
            new_lines.append(f'TELEGRAM_BOT_TOKEN="{TOKEN}"\n')
            has_token = True
        elif line.strip().startswith("TELEGRAM_CHAT_ID="):
            new_lines.append(f'TELEGRAM_CHAT_ID="{chat_id}"\n')
            has_chat_id = True
        else:
            new_lines.append(line)
            
    if not has_token:
        new_lines.append(f'TELEGRAM_BOT_TOKEN="{TOKEN}"\n')
    if not has_chat_id:
        new_lines.append(f'TELEGRAM_CHAT_ID="{chat_id}"\n')
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print(f"🟢 Configured .env with TELEGRAM_CHAT_ID={chat_id}!")
    return True

def main():
    print("🔄 Checking for Telegram messages to @presenceix_bot...")
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    try:
        res = requests.get(url, timeout=10).json()
        if not res.get("ok"):
            print(f"❌ Telegram API Error: {res}")
            return
            
        results = res.get("result", [])
        if not results:
            print("\n📥 No messages found yet.")
            print("👉 Action Required:")
            print("  1. Open your Telegram app.")
            print("  2. Search for: @presenceix_bot (or click https://t.me/presenceix_bot)")
            print("  3. Tap 'START' or send any message.")
            print("  4. Run this script again!\n")
            return
            
        # Get chat id from the latest update
        last_update = results[-1]
        message = last_update.get("message", last_update.get("edited_message", {}))
        chat_id = message.get("chat", {}).get("id")
        user_name = message.get("chat", {}).get("first_name", "there")
        
        if chat_id:
            print(f"🎉 Found active chat with {user_name} (ID: {chat_id})!")
            
            # Save to .env
            update_env(chat_id)
            
            # Send test message
            send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            welcome_text = (
                f"🎉 *PresenceIX AI Concierge Activated!*\n\n"
                f"Hello {user_name}! Your Telegram bot is now successfully linked to your phone.\n"
                f"Whenever your CRM receives or qualifies buyer leads, you will get real-time alerts right here! 🚀"
            )
            requests.post(send_url, json={
                "chat_id": chat_id,
                "text": welcome_text,
                "parse_mode": "Markdown"
            })
            print("🟢 Live confirmation message sent to your phone!")
        else:
            print("⚠️ Could not extract chat ID from message update.")
            
    except Exception as e:
        print(f"❌ Error linking Telegram: {e}")

if __name__ == "__main__":
    main()
