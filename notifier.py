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
            pass

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
        pass

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
            return False
    except Exception as e:
        print(f"[Phone Push Notification Error]: {e}")
        return False

def send_email_alert(email_cfg, product_name, stock_qty, price, product_url):
    """
    Send an urgent email alert.
    Supports zero-setup delivery via FormSubmit web API as well as standard SMTP fallback.
    """
    recipient = email_cfg.get("recipient_email", "manjunath10580@gmail.com")
    clean_name = product_name.encode("ascii", "ignore").decode("ascii").strip()

    # 1. Zero-Setup Delivery via FormSubmit API (No password/SMTP needed!)
    try:
        payload = {
            "Product": clean_name,
            "Status": "IN STOCK",
            "Available Stock": f"{stock_qty} packs",
            "Price": f"Rs. {price}",
            "Direct Buy Link": product_url,
            "_subject": f"🚨 [AMUL IN STOCK] {clean_name} Available Now!",
            "_template": "table"
        }
        headers = {
            "Referer": "https://github.com/Wandererre/amul-bot",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        res = requests.post(f"https://formsubmit.co/ajax/{recipient}", json=payload, headers=headers, timeout=12)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("success") == "true" or res_data.get("success") is True:
                print(f"📧 Email alert sent to {recipient}!")
                return True
            elif "activation" in res_data.get("message", "").lower():
                print(f"📧 FormSubmit activation email sent to {recipient}. Please click the link in your inbox once to activate free delivery.")
                return False
    except Exception as e:
        print(f"[Email Delivery Warning]: {e}")

    # 2. Fallback to standard SMTP if sender credentials are provided
    sender = email_cfg.get("sender_email")
    password = email_cfg.get("sender_password")
    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_cfg.get("smtp_port", 587)

    if sender and password:
        try:
            subject = f"[IN STOCK ALERT] {clean_name} Available on Amul Shop!"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: auto; border: 2px solid #28a745; border-radius: 8px; padding: 20px;">
                    <h2 style="color: #28a745;">🎉 Amul Whey Protein Stock Alert!</h2>
                    <p>The product you are tracking is now in stock:</p>
                    <p><b>Product:</b> {clean_name}</p>
                    <p><b>Stock:</b> {stock_qty} packs</p>
                    <p><b>Price:</b> Rs.{price}</p>
                    <div style="margin: 20px 0;">
                        <a href="{product_url}" style="background: #e50914; color: #fff; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 5px;">
                            BUY NOW ON AMUL SHOP
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            msg.attach(MIMEText(f"{clean_name} is in stock ({stock_qty} left) at Rs.{price}! Direct link: {product_url}", "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, [recipient], msg.as_string())

            print(f"📧 Email alert sent successfully via SMTP to {recipient}!")
            return True
        except Exception as e:
            print(f"[SMTP Error]: {e}")

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
        send_ntfy_alert(topic, name, stock, price, url)

    # 2. Email Notification (Zero-setup delivery to recipient_email)
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

    # 6. Auto Open Browser (Windows / Desktop)
    if config.get("auto_open_browser_on_stock", True) and os.name == "nt":
        try:
            print(f"🌐 Opening product page in browser: {url}")
            webbrowser.open(url)
        except Exception:
            pass
