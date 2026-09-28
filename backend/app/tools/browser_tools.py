from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission
from app.config import settings
from app.plugins.browser.manager import BrowserManager


class BrowserToolBase(BaseTool):
    def __init__(self, browser_manager: BrowserManager):
        super().__init__()
        self.browser = browser_manager


class OpenPageInput(ToolInputSchema):
    url: str
    headless: bool = Field(default=True)
    viewport: Optional[Dict[str, int]] = Field(default=None)


class OpenPageTool(BrowserToolBase):
    name = "open_page"
    description = "Open a web page"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = OpenPageInput
    
    async def execute(self, input_data: OpenPageInput) -> ToolOutput:
        try:
            page_id = await self.browser.open_page(
                input_data.url,
                headless=input_data.headless,
                viewport=input_data.viewport,
            )
            return ToolOutput(success=True, data={"page_id": page_id, "url": input_data.url})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class NavigateInput(ToolInputSchema):
    page_id: str
    url: str
    wait_until: str = Field(default="networkidle", pattern="^(load|domcontentloaded|networkidle|commit)$")


class NavigateTool(BrowserToolBase):
    name = "navigate"
    description = "Navigate to a URL in an existing page"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = NavigateInput
    
    async def execute(self, input_data: NavigateInput) -> ToolOutput:
        try:
            await self.browser.navigate(input_data.page_id, input_data.url, input_data.wait_until)
            return ToolOutput(success=True, data={"page_id": input_data.page_id, "url": input_data.url})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ExtractPageTextInput(ToolInputSchema):
    page_id: str
    selector: Optional[str] = Field(default=None)


class ExtractPageTextTool(BrowserToolBase):
    name = "extract_page_text"
    description = "Extract text content from a page"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.BROWSER_READ]
    input_schema = ExtractPageTextInput
    
    async def execute(self, input_data: ExtractPageTextInput) -> ToolOutput:
        try:
            text = await self.browser.extract_text(input_data.page_id, input_data.selector)
            return ToolOutput(success=True, data={"text": text})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class TakeScreenshotInput(ToolInputSchema):
    page_id: str
    path: Optional[str] = Field(default=None)
    full_page: bool = Field(default=False)


class TakeScreenshotTool(BrowserToolBase):
    name = "take_screenshot"
    description = "Take a screenshot of a page"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = TakeScreenshotInput
    
    async def execute(self, input_data: TakeScreenshotInput) -> ToolOutput:
        try:
            screenshot_path = await self.browser.take_screenshot(
                input_data.page_id,
                path=input_data.path,
                full_page=input_data.full_page,
            )
            return ToolOutput(success=True, data={"screenshot_path": screenshot_path})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ClickElementInput(ToolInputSchema):
    page_id: str
    selector: str
    wait_for_navigation: bool = Field(default=False)


class ClickElementTool(BrowserToolBase):
    name = "click_element"
    description = "Click an element on the page"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = ClickElementInput
    
    async def execute(self, input_data: ClickElementInput) -> ToolOutput:
        try:
            await self.browser.click(input_data.page_id, input_data.selector, input_data.wait_for_navigation)
            return ToolOutput(success=True, data={"selector": input_data.selector})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class FillFormInput(ToolInputSchema):
    page_id: str
    selector: str
    value: str


class FillFormTool(BrowserToolBase):
    name = "fill_form"
    description = "Fill a form field"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = FillFormInput
    
    async def execute(self, input_data: FillFormInput) -> ToolOutput:
        try:
            await self.browser.fill(input_data.page_id, input_data.selector, input_data.value)
            return ToolOutput(success=True, data={"selector": input_data.selector})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ClosePageInput(ToolInputSchema):
    page_id: str


class ClosePageTool(BrowserToolBase):
    name = "close_page"
    description = "Close a browser page"
    permission_level = PermissionLevel.SAFE_LOCAL
    required_permissions = [Permission.BROWSER_WRITE]
    input_schema = ClosePageInput
    
    async def execute(self, input_data: ClosePageInput) -> ToolOutput:
        try:
            await self.browser.close_page(input_data.page_id)
            return ToolOutput(success=True, data={"page_id": input_data.page_id})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))