from typing import Dict, Optional, Any
from uuid import uuid4
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings


class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
    
    async def start(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
    
    async def stop(self):
        for context in self._contexts.values():
            await context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._contexts.clear()
        self._pages.clear()
        self._playwright = None
        self._browser = None
    
    async def open_page(
        self,
        url: str,
        headless: bool = True,
        viewport: Optional[Dict[str, int]] = None,
    ) -> str:
        if not self._browser:
            await self.start()
        
        context = await self._browser.new_context(
            viewport=viewport or {"width": 1280, "height": 720},
        )
        page = await context.new_page()
        
        page_id = str(uuid4())
        self._contexts[page_id] = context
        self._pages[page_id] = page
        
        await page.goto(url, wait_until="networkidle")
        return page_id
    
    async def navigate(self, page_id: str, url: str, wait_until: str = "networkidle"):
        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        await page.goto(url, wait_until=wait_until)
    
    async def extract_text(self, page_id: str, selector: Optional[str] = None) -> str:
        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if selector:
            element = await page.query_selector(selector)
            if element:
                return await element.inner_text()
            return ""
        return await page.inner_text("body")
    
    async def take_screenshot(
        self,
        page_id: str,
        path: Optional[str] = None,
        full_page: bool = False,
    ) -> str:
        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if not path:
            import os
            os.makedirs(settings.DATA_DIR / "screenshots", exist_ok=True)
            path = str(settings.DATA_DIR / "screenshots" / f"{page_id}.png")
        
        await page.screenshot(path=path, full_page=full_page)
        return path
    
    async def click(self, page_id: str, selector: str, wait_for_navigation: bool = False):
        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if wait_for_navigation:
            async with page.expect_navigation():
                await page.click(selector)
        else:
            await page.click(selector)
    
    async def fill(self, page_id: str, selector: str, value: str):
        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        await page.fill(selector, value)
    
    async def close_page(self, page_id: str):
        context = self._contexts.pop(page_id, None)
        page = self._pages.pop(page_id, None)
        
        if context:
            await context.close()


browser_manager = BrowserManager()