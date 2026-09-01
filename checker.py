import os
import sys
import json
import asyncio
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "amul_profile")

async def check_amul_stock(pincode="721302", headless=True, timeout_seconds=35):
    """
    Launches browser with persistent context, sets/verifies pincode,
    and intercepts real-time product stock from Amul's API.
    Returns: list of product dictionaries
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    products_captured = []

    async with async_playwright() as p:
        # Launch persistent context to preserve login session and cookies
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=headless,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        async def on_response(response):
            if "ms.products" in response.url and "substore=" in response.url:
                try:
                    res_json = await response.json()
                    data = res_json.get("data", [])
                    if data:
                        products_captured.extend(data)
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            # Navigate to protein category page
            await page.goto("https://shop.amul.com/en/browse/protein", wait_until="networkidle", timeout=timeout_seconds * 1000)
            await asyncio.sleep(2)

            # Check if locationWidgetModal is open or if pincode needs to be entered
            modal = await page.query_selector("#locationWidgetModal")
            modal_visible = False
            if modal:
                cls = await modal.get_attribute("class") or ""
                modal_visible = "show" in cls

            # If modal is not open, check if current pincode in page matches desired pincode
            current_page_pincode = None
            try:
                storage_pincode = await page.evaluate("() => window.localStorage.getItem('pincode') || ''")
                current_page_pincode = storage_pincode.strip()
            except Exception:
                pass

            if modal_visible or current_page_pincode != str(pincode):
                # We need to set the pincode
                if not modal_visible:
                    pincode_btn = await page.query_selector(".pincode_wrap, [data-bs-target='#locationWidgetModal'], [href='#locationWidgetModal']")
                    if pincode_btn:
                        await pincode_btn.click()
                        await asyncio.sleep(1.5)

                search_input = await page.query_selector("#locationWidgetModal input#search, input[placeholder*='pincode' i]")
                if search_input:
                    await search_input.fill(str(pincode))
                    await asyncio.sleep(2)

                    # Look for matching suggestion in dropdown
                    suggestion = await page.query_selector("a.searchitem-name, .list-group-item a")
                    if suggestion:
                        await suggestion.click()
                        await asyncio.sleep(4)
                    else:
                        await search_input.press("Enter")
                        await asyncio.sleep(4)

            # Wait a few moments for the products API to be intercepted
            for _ in range(8):
                if products_captured:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[Browser Check Warning]: {e}")
        finally:
            await context.close()

    # Normalize captured products
    formatted_products = []
    seen_aliases = set()

    for p in products_captured:
        alias = p.get("alias", "")
        if alias in seen_aliases:
            continue
        seen_aliases.add(alias)

        name = p.get("name", "Unknown Product")
        available = bool(p.get("available"))
        stock = p.get("inventory_quantity", 0)
        price = p.get("price", 0)
        sku = p.get("sku", "")
        url = f"https://shop.amul.com/en/product/{alias}" if alias else "https://shop.amul.com/en/browse/protein"

        # An item is in stock if available is True and stock > 0
        is_in_stock = available and (stock > 0)

        formatted_products.append({
            "name": name,
            "alias": alias,
            "sku": sku,
            "price": price,
            "available": available,
            "inventory_quantity": stock,
            "in_stock": is_in_stock,
            "url": url
        })

    return formatted_products

def run_sync_check(pincode="721302", headless=True):
    """Helper to run async check synchronously."""
    return asyncio.run(check_amul_stock(pincode=pincode, headless=headless))
