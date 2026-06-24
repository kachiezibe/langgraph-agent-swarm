import os
import requests
import urllib.parse

def send_telegram_message(text: str) -> bool:
    """
    Sends a message to a Telegram chat using a custom Telegram Bot.
    This is 100% free and instant.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    
    # Strip basic HTML tags if any, or use markdown/HTML format
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("🟢 [Notification] Telegram notification sent successfully!")
            return True
        else:
            print(f"⚠️ [Notification] Telegram returned status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ [Notification] Telegram exception: {e}")
        return False


def send_slack_message(text: str) -> bool:
    """
    Sends a message to a Slack channel using an Incoming Webhook.
    This is 100% free and instant.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    
    try:
        payload = {
            "text": text
        }
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code == 200:
            print("🟢 [Notification] Slack notification sent successfully!")
            return True
        else:
            print(f"⚠️ [Notification] Slack returned status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ [Notification] Slack exception: {e}")
        return False


def send_whatsapp_cloud_api_message(text: str, recipient_phone: str) -> bool:
    """
    Sends a message using the Meta WhatsApp Business Cloud API.
    Meta provides 1,000 conversations/month completely free of charge.
    """
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id or not recipient_phone:
        return False
    
    # Strip non-digits from phone number
    clean_phone = "".join(filter(str.isdigit, recipient_phone))
    if not clean_phone:
        return False
        
    try:
        url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": text
            }
        }
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code in [200, 201]:
            print("🟢 [Notification] WhatsApp Cloud API message sent successfully!")
            return True
        else:
            print(f"⚠️ [Notification] WhatsApp Cloud API returned status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ [Notification] WhatsApp Cloud API exception: {e}")
        return False


def get_whatsapp_click_to_chat_url(text: str, recipient_phone: str) -> str:
    """
    Generates a WhatsApp click-to-chat link. 
    Opening this link opens the WhatsApp app with prefilled text and recipient.
    This requires absolutely zero setup and is 100% free.
    """
    clean_phone = "".join(filter(str.isdigit, recipient_phone)) if recipient_phone else ""
    encoded_text = urllib.parse.quote(text)
    if clean_phone:
        return f"https://wa.me/{clean_phone}?text={encoded_text}"
    return f"https://wa.me/?text={encoded_text}"


def trigger_all_notifications(text: str, recipient_phone: str = None) -> dict:
    """
    Convenience method to trigger all active and configured notifications.
    Safely bypasses any unconfigured channels.
    """
    results = {}
    
    # Format message headers for admin clarity
    formatted_text = f"🔔 *PresenceIX AI Concierge Notification*\n\n{text}"
    
    # Trigger Telegram
    results["telegram"] = send_telegram_message(formatted_text)
    
    # Trigger Slack
    results["slack"] = send_slack_message(formatted_text)
    
    # Trigger WhatsApp Cloud
    if recipient_phone:
        results["whatsapp_cloud"] = send_whatsapp_cloud_api_message(text, recipient_phone)
        results["whatsapp_link"] = get_whatsapp_click_to_chat_url(text, recipient_phone)
    else:
        alert_phone = os.getenv("ALERT_PHONE_NUMBER")
        if alert_phone:
            results["whatsapp_cloud"] = send_whatsapp_cloud_api_message(text, alert_phone)
            results["whatsapp_link"] = get_whatsapp_click_to_chat_url(text, alert_phone)
            
    return results


def notify_admin_new_lead(lead_id: str, name: str, phone: str, email: str, source: str, enriched_info: str, initial_greeting: str) -> dict:
    """
    Sends a beautiful, formatted admin alert about a brand new lead ingestion to Telegram and Slack.
    """
    # Parse basic enrichment details if present
    simulated_property = "N/A"
    neighborhood_price = "N/A"
    
    if enriched_info:
        for line in enriched_info.split("\n"):
            line_lower = line.lower()
            if "clicked" in line_lower or "address" in line_lower or "property" in line_lower:
                parts = line.split(":")
                simulated_property = parts[1].strip() if len(parts) > 1 else line.strip()
            elif "neighborhood" in line_lower or "price" in line_lower or "median" in line_lower or "$" in line:
                parts = line.split(":")
                neighborhood_price = parts[1].strip() if len(parts) > 1 else line.strip()

    text = (
        f"🆕 *PRESENCEIX: New Lead Ingested!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name*: {name}\n"
        f"📞 *Phone*: {phone}\n"
        f"📧 *Email*: {email}\n"
        f"🚦 *Source*: {source}\n"
        f"🆔 *Lead ID*: `{lead_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Property*: {simulated_property}\n"
        f"💰 *Est. Price*: {neighborhood_price}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 *Initial Outreach SMS Drafted*:\n"
        f"\"{initial_greeting}\""
    )
    
    results = {}
    results["telegram"] = send_telegram_message(text)
    results["slack"] = send_slack_message(text)
    return results


def notify_admin_assessment(lead_id: str, name: str, final_score: float, scores: dict, status: str, latest_client_msg: str, agent_response: str) -> dict:
    """
    Sends a detailed qualification assessment report to admin channels (Telegram and Slack).
    """
    status_emoji = "🟢" if status == "QUALIFIED" else "🟡" if status == "NURTURE" else "🔴"
    
    text = (
        f"📊 *PRESENCEIX: Qualification Assessment*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Lead*: {name}\n"
        f"🆔 *ID*: `{lead_id}`\n"
        f"⚖️ *Status*: {status_emoji} *{status}*\n"
        f"📈 *Final Score*: `{final_score}/10.0`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧮 *Subscores*:\n"
        f"  - 💵 Budget: `{scores.get('budget', 1.0)}/10.0`\n"
        f"  - 📅 Timeline: `{scores.get('timeline', 1.0)}/10.0`\n"
        f"  - ❤️ Motivation: `{scores.get('motivation', 1.0)}/10.0`\n"
        f"  - 🤝 Agent Rep: `{scores.get('representation', 1.0)}/10.0`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 *Latest Client Reply*:\n"
        f"\"{latest_client_msg}\"\n\n"
        f"📤 *Agent Concierge Response*:\n"
        f"\"{agent_response}\""
    )
    
    results = {}
    results["telegram"] = send_telegram_message(text)
    results["slack"] = send_slack_message(text)
    return results


def send_client_sms(text: str, recipient_phone: str) -> dict:
    """
    Sends conversational SMS replies to the client's phone via WhatsApp Cloud API.
    Bypasses Admin alerting channels (Telegram and Slack) to prevent spam.
    """
    results = {}
    if recipient_phone:
        results["whatsapp_cloud"] = send_whatsapp_cloud_api_message(text, recipient_phone)
        results["whatsapp_link"] = get_whatsapp_click_to_chat_url(text, recipient_phone)
    else:
        alert_phone = os.getenv("ALERT_PHONE_NUMBER")
        if alert_phone:
            results["whatsapp_cloud"] = send_whatsapp_cloud_api_message(text, alert_phone)
            results["whatsapp_link"] = get_whatsapp_click_to_chat_url(text, alert_phone)
    return results
