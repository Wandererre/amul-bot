# 🥛 Amul Whey Protein Stock Tracker Bot (100% Free)

A reliable, automated stock tracker built specifically for `shop.amul.com`. It monitors Amul Whey Protein sachets (**Chocolate 60 Sachets** & **Chocolate 30 Sachets**) for your delivery pincode (`721302`), uses your authenticated session, and triggers instant phone, email, and desktop alerts the moment stock drops into the warehouse.

---

## 📱 Mobile & Email Alerts (Works on Institute Wi-Fi)

Since Telegram is blocked on institute Wi-Fi, the bot includes two free alternatives:

### 1. Instant Phone Push Alert (Zero Sign-up, Never Blocked)
The bot uses **ntfy.sh**, a 100% free, open-source notification system that operates over standard HTTPS (bypassing campus firewalls):
1. On your Android phone or iPhone, install the free **ntfy** app (from Google Play Store or Apple App Store). Or simply open [ntfy.sh/amul_whey_manjunath_721302](https://ntfy.sh/amul_whey_manjunath_721302) in your phone's browser.
2. In the app, tap **+ (Subscribe)** and enter the topic: `amul_whey_manjunath_721302`.
3. That's it! When stock drops, your phone will ring with an urgent high-priority notification and a direct one-click link to buy!

### 2. Email Notification (to `manjunath10580@gmail.com`)
The bot sends an urgent HTML email with the direct product buy link:
1. Go to your Google Account: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
2. Generate an **App Password** (name it "Amul Bot").
3. Open `config.json` and enter your sender email and 16-character App Password:
```json
"email": {
  "enabled": true,
  "recipient_email": "manjunath10580@gmail.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "YOUR_GMAIL@gmail.com",
  "sender_password": "YOUR_16_DIGIT_APP_PASSWORD"
}
```

---

## ☁️ Running 24/7 (Cloud vs Local)

> [!WARNING]
> **Why PythonAnywhere Free Tier Doesn't Work**:
> PythonAnywhere's free tier enforces a strict outbound HTTP proxy whitelist that blocks non-whitelisted sites like `shop.amul.com`. It also lacks the libraries required to run Chromium.

### Best Free 24/7 Options:

#### Option A: Run Silently on Your PC (Easiest)
- Double-click **`run_background.vbs`**.
- It runs the bot completely invisibly in the background on your Windows machine without keeping any terminal window open.
- To stop it anytime, double-click **`stop_background.bat`**.

#### Option B: GitHub Actions 24/7 Cloud Runner (Free, PC can be OFF)
We have included a pre-configured GitHub Actions workflow at `.github/workflows/check_stock.yml`:
1. Create a private GitHub repository and push this folder to it.
2. In GitHub repo Settings -> Secrets and variables -> Actions, add your `GMAIL_USER` and `GMAIL_APP_PASS`.
3. GitHub will run the stock check automatically on cloud servers every 5 minutes 24/7, sending phone/email alerts even when your laptop is completely turned off!

---

## 🚀 Commands Quick Reference

- **Double-click `run_bot.bat`** or `python bot.py`: Start real-time monitoring console.
- **Double-click `run_background.vbs`**: Run silently in the background.
- **Double-click `stop_background.bat`**: Stop background instances.
- **`python bot.py --check`**: Perform a single immediate check and print stock table.
- **`python bot.py --test-alert`**: Test the audio alarm, phone push, email, and browser launch.
- **`python bot.py --setup`**: Open visible Chrome to log in to your Amul account once.
