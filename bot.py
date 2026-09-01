import os
import sys
import time
import random
import json
import argparse
import asyncio
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console(force_terminal=True, legacy_windows=False)

from checker import check_amul_stock, BASE_DIR, PROFILE_DIR
from notifier import trigger_all_alerts, play_audio_alarm, show_windows_toast

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[bold red]Error loading config.json: {e}[/bold red]")
    return {
        "pincode": "721302",
        "check_interval_seconds": 90,
        "jitter_seconds": 15,
        "auto_open_browser_on_stock": True,
        "sound_alarm": True,
        "desktop_notification": True,
        "targets": [
            {
                "name": "Amul Chocolate Whey Protein (60 Sachets)",
                "alias": "amul-chocolate-whey-protein-34-g-or-pack-of-60-sachets",
                "url": "https://shop.amul.com/en/product/amul-chocolate-whey-protein-34-g-or-pack-of-60-sachets"
            },
            {
                "name": "Amul Chocolate Whey Protein (30 Sachets)",
                "alias": "amul-chocolate-whey-protein-34-g-or-pack-of-30-sachets",
                "url": "https://shop.amul.com/en/product/amul-chocolate-whey-protein-34-g-or-pack-of-30-sachets"
            }
        ],
        "track_all_whey_sachets": False
    }

def print_header(pincode, targets):
    console.print(Panel.fit(
        f"[bold cyan]Amul Whey Protein Stock Checker[/bold cyan]\n"
        f"[yellow]Delivery Pincode:[/yellow] [bold white]{pincode}[/bold white]\n"
        f"[yellow]Tracking Targets:[/yellow] [bold green]{len(targets)} target products[/bold green]\n"
        f"[dim]Runs locally 24/7 • Cloudflare bypass • Persistent profile session[/dim]",
        border_style="cyan"
    ))

async def interactive_setup():
    """Opens a visible browser for the user to log in and set up their session once."""
    from playwright.async_api import async_playwright
    os.makedirs(PROFILE_DIR, exist_ok=True)
    console.print(Panel.fit(
        "[bold green]Interactive Login & Setup Mode[/bold green]\n\n"
        "1. A Chrome browser window will now open.\n"
        "2. Log in to your Amul account (enter mobile number / OTP if requested).\n"
        "3. Enter your delivery pincode in the delivery location selector.\n"
        "4. Once you are logged in, close the browser window or return here and press ENTER.",
        border_style="green"
    ))

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://shop.amul.com/login", wait_until="load")

        console.print("\n[bold yellow]Browser is open. Waiting for you to finish logging in...[/bold yellow]")
        try:
            await asyncio.to_thread(input, "\nPress ENTER here after you have finished logging in on the browser: ")
        except Exception:
            pass
        finally:
            await context.close()

    console.print("[bold green]Setup complete! Session and credentials saved to persistent profile.[/bold green]\n")

def filter_watched_products(products, config):
    """Filters product list based on target aliases or keywords."""
    targets = config.get("targets", [])
    target_aliases = {t.get("alias") for t in targets if t.get("alias")}
    track_all = config.get("track_all_whey_sachets", False)

    matched = []
    for p in products:
        alias = p.get("alias", "")
        name = p.get("name", "").lower()

        if alias in target_aliases:
            matched.append((p, True))
        elif track_all and ("whey" in name or "sachet" in name):
            matched.append((p, False))

    return matched

def display_product_table(products, config):
    """Render a clean status table without unsupported terminal glyphs."""
    table = Table(title=f"Amul Whey Stock Status ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})", border_style="blue")
    table.add_column("Status", justify="center", style="bold")
    table.add_column("Product Name", style="white")
    table.add_column("Stock", justify="right")
    table.add_column("Price", justify="right", style="green")

    target_aliases = {t.get("alias") for t in config.get("targets", [])}

    for p in products:
        name = p.get("name", "")
        if "whey" not in name.lower() and "sachet" not in name.lower():
            continue

        alias = p.get("alias", "")
        is_target = alias in target_aliases
        stock = p.get("inventory_quantity", 0)
        is_in_stock = p.get("in_stock", False)
        price = f"Rs.{p.get('price', 0)}"

        if is_in_stock:
            status_text = "[bold green][IN STOCK][/bold green]"
            stock_text = f"[bold green]{stock}[/bold green]"
        else:
            status_text = "[bold red][SOLD OUT][/bold red]"
            stock_text = "[dim]0[/dim]"

        display_name = f"[bold]{name}[/bold] [cyan][TARGET][/cyan]" if is_target else name
        table.add_row(status_text, display_name, stock_text, price)

    console.print(table)

async def check_once(config):
    pincode = config.get("pincode", "721302")
    console.print(f"\n[cyan]Checking stock for pincode [bold]{pincode}[/bold]...[/cyan]")
    products = await check_amul_stock(pincode=pincode, headless=True)
    if not products:
        console.print("[bold red]Failed to retrieve product data. Retrying next cycle.[/bold red]")
        return []

    display_product_table(products, config)
    return products

async def monitor_loop(config):
    pincode = config.get("pincode", "721302")
    interval = config.get("check_interval_seconds", 90)
    jitter = config.get("jitter_seconds", 15)
    targets = config.get("targets", [])

    print_header(pincode, targets)
    console.print("[green]Press Ctrl+C at any time to stop the bot.[/green]\n")

    alerted_aliases = set()
    iteration = 1

    while True:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            console.print(f"[bold cyan][Run #{iteration} - {timestamp}][/bold cyan] Checking Amul warehouse for pincode {pincode}...")
            products = await check_amul_stock(pincode=pincode, headless=True)

            if products:
                matched = filter_watched_products(products, config)
                display_product_table(products, config)

                for product, is_target in matched:
                    alias = product.get("alias")
                    if product.get("in_stock"):
                        if alias not in alerted_aliases:
                            alerted_aliases.add(alias)
                            trigger_all_alerts(product, config)
                    else:
                        # Reset alert if product goes back to out-of-stock
                        if alias in alerted_aliases:
                            alerted_aliases.remove(alias)
            else:
                console.print("[yellow]No products received from API response this cycle.[/yellow]")

            iteration += 1

            sleep_time = interval + random.randint(-jitter, jitter)
            sleep_time = max(30, sleep_time)
            console.print(f"[dim]Next check in {sleep_time}s...[/dim]\n")
            await asyncio.sleep(sleep_time)

        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n[bold yellow]Stock checker stopped by user.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected error in monitor loop: {e}[/bold red]")
            await asyncio.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Amul Whey Protein Sachets Stock Tracker Bot")
    parser.add_argument("--setup", action="store_true", help="Launch visible browser for one-time login & pincode setup")
    parser.add_argument("--check", action="store_true", help="Perform a single stock check and display results")
    parser.add_argument("--test-alert", action="store_true", help="Test sound alarm, Windows toast, and browser opening")
    args = parser.parse_args()

    config = load_config()

    if args.setup:
        asyncio.run(interactive_setup())
    elif args.test_alert:
        console.print("[bold yellow]Testing alert system...[/bold yellow]")
        sample_prod = {
            "name": "Amul Chocolate Whey Protein (60 Sachets) [TEST]",
            "inventory_quantity": 50,
            "price": 4500,
            "url": "https://shop.amul.com/en/product/amul-chocolate-whey-protein-34-g-or-pack-of-60-sachets"
        }
        trigger_all_alerts(sample_prod, config)
        console.print("[bold green]Test alerts executed successfully![/bold green]")
    elif args.check:
        asyncio.run(check_once(config))
    else:
        asyncio.run(monitor_loop(config))

if __name__ == "__main__":
    main()
