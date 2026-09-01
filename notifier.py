import os
import sys
import time
import threading
import subprocess
import webbrowser
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def play_audio_alarm(repeat=4):
    """Play a loud, attention-grabbing alert sound on Windows using winsound."""
    def _beep():
        try:
            import winsound
            for _ in range(repeat):
                winsound.Beep(1200, 250)
                time.sleep(0.08)
                winsound.Beep(1600, 300)
                time.sleep(0.08)
                winsound.Beep(2000, 450)
                time.sleep(0.4)
        except Exception as e:
            print(f"\a[Audio Alarm Error: {e}]\a")

    thread = threading.Thread(target=_beep, daemon=True)
    thread.start()

def show_windows_toast(title, message):
    """Show a native Windows desktop balloon / toast notification."""
    try:
        clean_title = title.replace('"', '').replace("'", "")
        clean_msg = message.replace('"', '').replace("'", "")
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = "{clean_title}"
        $notification.BalloonTipText = "{clean_msg}"
        $notification.Visible = $true
        $notification.ShowBalloonTip(10000)
        Start-Sleep -Seconds 2
        $notification.Dispose()
        """
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
    except Exception as e:
        print(f"[Toast Notification Error]: {e}")

def send_ntfy_alert(topic, product_name, stock_qty, price, product_url):
    """
    Send an instant, 100% free push notification to your phone via ntfy.sh.
    Never blocked on institute Wi-Fi because it runs over standard HTTPS.
    Install the free 'ntfy' app on Android/iPhone and subscribe to your topic!
    """
    if not topic:
        return False
    try:
        url = f"https://ntfy.sh/{topic.strip()}"
        # Keep headers clean ASCII to prevent latin-1 HTTP header errors
        clean_name = product_name.encode("ascii", "ignore").decode("ascii").strip()
        title = f"[IN STOCK] {clean_name}"
        body = f"Stock: {stock_qty} packs | Price: Rs.{price}\nClick to buy immediately on Amul Shop!"
        headers = {
            "Title": title,
            "Priority": "urgent",
            "Tags": "warning,shopping_trolley",
            "Click": product_url
        }
        res = requests.post(url, data=body.encode("utf-8"), headers=headers, timeout=10)
        if res.status_code == 200:
            print(f"📲 Push notification successfully sent to phone via ntfy.sh/{topic.strip()}!")
            return True
        else:
            print(f"[ntfy.sh response]: {res.status_code}")
            return False
    except Exception as e:
        print(f"[Phone Push Notification Error]: {e}")
        return False

def send_email_alert(email_cfg, product_name, stock_qty, price, product_url):
    """
    Send an urgent email alert via SMTP.
    """
    recipient = email_cfg.get("recipient_email", "manjunath10580@gmail.com")
    sender = email_cfg.get("sender_email")
    password = email_cfg.get("sender_password")
    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_cfg.get("smtp_port", 587)

    if not sender or not password:
        print(f"\n[Email Info] Ready to send to {recipient}. To activate, set your Gmail 'sender_email' and 'sender_password' (App Password) in config.json.")
        return False

    try:
        subject = f"[IN STOCK ALERT] {product_name} Available on Amul Shop!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: auto; border: 2px solid #28a745; border-radius: 8px; padding: 20px;">
                <h2 style="color: #28a745; margin-top: 0;">Amul Whey Protein Stock Alert!</h2>
                <p>Great news! The product you are monitoring is now available to order for your pincode:</p>
                <div style="background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0;">
                    <h3 style="margin: 0 0 10px 0;">{product_name}</h3>
                    <p style="margin: 5px 0;"><b>Stock Available:</b> <span style="color: #28a745; font-size: 1.2em;">{stock_qty} packs</span></p>
                    <p style="margin: 5px 0;"><b>Price:</b> Rs.{price}</p>
                </div>
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{product_url}" style="background-color: #e50914; color: white; padding: 14px 28px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 6px; display: inline-block;">
                        BUY NOW ON AMUL SHOP
                    </a>
                </div>
                <p style="font-size: 12px; color: #777;">Hurry up before stock runs out! This is an automated notification from your personal Amul Stock Tracker.</p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.attach(MIMEText(f"{product_name} is in stock ({stock_qty} left) at Rs.{price}! Direct link: {product_url}", "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())

        print(f"📧 Email alert sent successfully to {recipient}!")
        return True
    except Exception as e:
        print(f"[Email Notification Error]: {e}")
        return False

def send_whatsapp_alert(phone_number, apikey, product_name, stock_qty, price, product_url):
    """Send free WhatsApp message via CallMeBot API."""
    if not phone_number or not apikey:
        return False
    try:
        clean_name = product_name.encode("ascii", "ignore").decode("ascii").strip()
        text = f"*AMUL STOCK ALERT!*\n\n*{clean_name}* is IN STOCK!\nAvailable: {stock_qty} units\nPrice: Rs.{price}\n\nBuy Now: {product_url}"
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={requests.utils.quote(text)}&apikey={apikey}"
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[WhatsApp Alert Error]: {e}")
        return False

def trigger_all_alerts(product, config):
    """Triggers all configured alert channels for an in-stock product."""
    name = product.get("name", "Amul Whey Protein")
    stock = product.get("inventory_quantity", "Available")
    price = product.get("price", "N/A")
    url = product.get("url", f"https://shop.amul.com/en/product/{product.get('alias', '')}")

    print("\n" + "=" * 60)
    print(f"[ALERT] IN STOCK: {name} (Stock: {stock}, Price: Rs.{price})")
    print(f"Direct Buy URL: {url}")
    print("=" * 60 + "\n")

    # 1. Phone Push Notification via ntfy (Works on Institute WiFi without Telegram)
    ntfy_cfg = config.get("phone_push_ntfy", {})
    if ntfy_cfg.get("enabled", True):
        topic = ntfy_cfg.get("topic", "amul_whey_manjunath_721302")
        print(f"📲 Sending instant push alert to phone (ntfy.sh/{topic})...")
        send_ntfy_alert(topic, name, stock, price, url)

    # 2. Email Notification
    email_cfg = config.get("email", {})
    if email_cfg.get("enabled", True):
        send_email_alert(email_cfg, name, stock, price, url)

    # 3. WhatsApp Notification
    wa_cfg = config.get("whatsapp", {})
    if wa_cfg.get("enabled") and wa_cfg.get("phone_number") and wa_cfg.get("callmebot_apikey"):
        send_whatsapp_alert(wa_cfg["phone_number"], wa_cfg["callmebot_apikey"], name, stock, price, url)

    # 4. Audio Alarm (Windows)
    if config.get("sound_alarm", True):
        play_audio_alarm(repeat=5)

    # 5. Desktop Toast (Windows)
    if config.get("desktop_notification", True):
        show_windows_toast(
            title="Amul Stock Alert! In Stock Now!",
            message=f"{name} is IN STOCK ({stock} units available) at Rs.{price}!"
        )

    # 6. Auto Open Browser
    if config.get("auto_open_browser_on_stock", True):
        try:
            print(f"🌐 Opening product page in browser: {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"[Browser Launch Error]: {e}")
