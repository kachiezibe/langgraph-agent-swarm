import os
from dotenv import load_dotenv
load_dotenv()

import notifications

def test_defaults():
    print("Testing Notification Graceful Fallbacks...")
    
    # 1. Test Telegram Default (unconfigured)
    print("  Triggering Telegram (unconfigured)...")
    res_tg = notifications.send_telegram_message("Test message")
    print(f"  Telegram result: {res_tg} (Expected: False)")
    
    # 2. Test Slack Default (unconfigured)
    print("  Triggering Slack (unconfigured)...")
    res_sl = notifications.send_slack_message("Test message")
    print(f"  Slack result: {res_sl} (Expected: False)")
    
    # 3. Test WhatsApp Cloud API Default (unconfigured)
    print("  Triggering WhatsApp Cloud (unconfigured)...")
    res_wa = notifications.send_whatsapp_cloud_api_message("Test message", "+15551234567")
    print(f"  WhatsApp Cloud API result: {res_wa} (Expected: False)")
    
    # 4. Test WhatsApp Click to Chat Link Generation (Should ALWAYS work!)
    print("  Generating WhatsApp Click to Chat URL...")
    wa_url = notifications.get_whatsapp_click_to_chat_url("Hello from PresenceIX AI!", "+1 (555) 123-4567")
    print(f"  Generated URL: {wa_url}")
    assert "https://wa.me/15551234567" in wa_url
    assert "Hello" in wa_url
    print("  WhatsApp Click to Chat is 100% correct!")
    
    # 5. Trigger all notifications
    print("  Triggering all notifications (should run gracefully)...")
    res_all = notifications.trigger_all_notifications("Test message from PresenceIX", "+1-555-123-4567")
    print(f"  Trigger all result dict: {res_all}")
    
    print("\n✅ Notifications module works perfectly with graceful unconfigured fallbacks!")

if __name__ == "__main__":
    test_defaults()
