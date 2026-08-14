import asyncio
import os
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.browser.tool import NavigateTool, ClickTool, ScreenshotTool, ScrollTool
from raavone_tools.filesystem.provider import FilesystemProvider
from raavone_tools.filesystem.tool import ReadFileTool, WriteFileTool, ListDirTool

async def main():
    print("🚀 Initializing ToolManager...")
    manager = ToolManager()
    
    # 1. Setup Providers
    # Filesystem: Create a 'sandbox' directory in current folder
    sandbox_dir = Path("./sandbox")
    sandbox_dir.mkdir(exist_ok=True)
    
    fs_provider = FilesystemProvider(workspace_root=sandbox_dir)
    browser_provider = BrowserProvider(headless=True) # Runs in headless mode (no window pops up)
    
    # Register filesystem tools
    manager.register_tool(WriteFileTool(provider=fs_provider))
    manager.register_tool(ReadFileTool(provider=fs_provider))
    manager.register_tool(ListDirTool(provider=fs_provider))
    
    # Register browser tools
    manager.register_tool(NavigateTool(provider=browser_provider))
    manager.register_tool(ClickTool(provider=browser_provider))
    manager.register_tool(ScreenshotTool(provider=browser_provider))
    manager.register_tool(ScrollTool(provider=browser_provider))
    
    # Initialize all registered providers
    print("🔧 Initializing browser and filesystem providers...")
    await manager.initialize_providers()
    
    try:
        # 2. Browser Action: Navigate to .sethunaachi.shop.dev
        print("\n🌐 [Browser] Navigating to https://www.sethunaachi.shop/...")
        nav_result = await manager.execute("navigate", {"url": "https://www.sethunaachi.shop/", "wait_until": "networkidle"})
        print(f"✅ Page Title: {nav_result.get('title')}")
        
        # Scroll down before taking screenshot
        print("📜 [Browser] Scrolling down 800 pixels...")
        scroll_result = await manager.execute("scroll", {"direction": "down", "amount": 800})
        print(f"✅ Scroll status: {scroll_result.get('status')} - {scroll_result.get('message')}")
        
        # 3. Browser Action: Take a screenshot
        screenshot_path = sandbox_dir / ".sethunaachi.shop_home.png"
        print(f"📸 [Browser] Taking screenshot and saving to sandbox/.sethunaachi.shop_home.png...")
        shot_result = await manager.execute("screenshot", {"path": str(screenshot_path)})
        print(f"✅ Screenshot success: {shot_result.get('status')}")
        
        # 4. Filesystem Action: Create a log/report file
        print("\n📁 [Filesystem] Writing audit report to sandbox/report.txt...")
        report_content = f"Execution Audit Log:\n- Successfully navigated to: {nav_result.get('title')}\n- Saved screenshot to: .sethunaachi.shop_home.png\n"
        write_result = await manager.execute(
            "write_file", 
            {"path": "report.txt", "content": report_content}
        )
        print(f"✅ Bytes written: {write_result.get('bytes_written')}")
        
        # 5. Filesystem Action: Read the report file back
        print("📖 [Filesystem] Reading sandbox/report.txt content:")
        read_result = await manager.execute("read_file", {"path": "report.txt"})
        print("-" * 40)
        print(read_result.get("content"))
        print("-" * 40)
        
        # 6. Filesystem Action: List the directory files
        print("🗂️ [Filesystem] Listing files inside sandbox:")
        list_result = await manager.execute("list_dir", {"path": "."})
        for item in list_result.get("items", []):
            print(f"  - {item['name']} ({item['type']}, {item.get('size', 0)} bytes)")
            
    finally:
        # Always clean up providers
        print("\n🧹 Cleaning up browser session...")
        await manager.close_providers()

if __name__ == "__main__":
    asyncio.run(main())
