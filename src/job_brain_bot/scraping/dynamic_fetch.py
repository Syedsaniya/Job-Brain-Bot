async def fetch_dynamic_html_async(url: str, timeout_ms: int) -> str:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            await page.wait_for_timeout(800)
            return await page.content()
        except PlaywrightTimeoutError:
            return ""
        finally:
            await browser.close()
