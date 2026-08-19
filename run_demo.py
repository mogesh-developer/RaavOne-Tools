import asyncio
import os
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.browser.tool import NavigateTool, ClickTool, ScreenshotTool, ScrollTool, ExtractTool
from raavone_tools.filesystem.provider import FilesystemProvider
from raavone_tools.filesystem.tool import ReadFileTool, WriteFileTool, ListDirTool
from raavone_tools.http.provider import HttpProvider
from raavone_tools.http.tool import HttpGetTool, HttpPostTool, HttpDownloadTool, HttpPutTool, HttpPatchTool, HttpDeleteTool

async def main():
    print("🚀 Initializing ToolManager...")
    manager = ToolManager()
    
    # 1. Setup Providers
    sandbox_dir = Path("./sandbox")
    sandbox_dir.mkdir(exist_ok=True)
    
    fs_provider = FilesystemProvider(workspace_root=sandbox_dir)
    browser_provider = BrowserProvider(headless=True) # Runs in headless mode (no window pops up)
    http_provider = HttpProvider()
    
    # Register filesystem tools
    manager.register_tool(WriteFileTool(provider=fs_provider))
    manager.register_tool(ReadFileTool(provider=fs_provider))
    manager.register_tool(ListDirTool(provider=fs_provider))
    
    # Register browser tools
    manager.register_tool(NavigateTool(provider=browser_provider))
    manager.register_tool(ClickTool(provider=browser_provider))
    manager.register_tool(ScreenshotTool(provider=browser_provider))
    manager.register_tool(ScrollTool(provider=browser_provider))
    manager.register_tool(ExtractTool(provider=browser_provider))

    # Register HTTP tools
    manager.register_tool(HttpGetTool(provider=http_provider))
    manager.register_tool(HttpPostTool(provider=http_provider))
    manager.register_tool(HttpPutTool(provider=http_provider))
    manager.register_tool(HttpPatchTool(provider=http_provider))
    manager.register_tool(HttpDeleteTool(provider=http_provider))
    manager.register_tool(HttpDownloadTool(provider=http_provider))
    
    # Initialize all registered providers
    print("🔧 Initializing browser, filesystem, and HTTP providers...")
    await manager.initialize_providers()
    
    try:
        # 2. Browser Action: Navigate to .sethunaachi.shop.dev
        print("\n🌐 [Browser] Navigating to https://mogeshdev.vercel.app/...")
        nav_result = await manager.execute("navigate", {"url": "https://mogeshdev.vercel.app/", "wait_until": "networkidle"})
        print(f"✅ Page Title: {nav_result.get('title')}")
        
        # Scroll down before taking screenshot
        print("📜 [Browser] Scrolling down 800 pixels...")
        scroll_result = await manager.execute("scroll", {"direction": "down", "amount": 800})
        print(f"✅ Scroll status: {scroll_result.get('status')} - {scroll_result.get('message')}")
        
        # 3. Browser Action: Take a screenshot
        screenshot_path = sandbox_dir / ".sethunaachi.shop_home.png"
        print(f"📸 [Browser] Taking screenshot and saving to sandbox/.sethunaachi.shop_home.png...")
        shot_result = await manager.execute("screenshot", {"path": str(screenshot_path)})
        # 3a. Browser Action: Extract page contents (links)
        print("\n🔍 [Browser] Extracting links from the portfolio page...")
        extract_result = await manager.execute("extract", {"mode": "links"})
        print(f"✅ Extracted {len(extract_result.get('data', []))} links from page.")
        
        # Save extracted links to JSON via filesystem write_file
        import json
        links_json = json.dumps(extract_result.get('data', []), indent=2)
        print("📁 [Filesystem] Saving extracted links to sandbox/extracted_links.json...")
        await manager.execute("write_file", {"path": "extracted_links.json", "content": links_json})

        # 4. HTTP Action: GET request to JSONPlaceholder API
        print("\n⚡ [HTTP] Sending GET request to jsonplaceholder.typicode.com...")
        get_res = await manager.execute("http_get", {"url": "https://jsonplaceholder.typicode.com/posts/1"})
        print(f"✅ GET Status: {get_res.get('status_code')}")
        print(f"📦 Response Body: {get_res.get('body')}")

        # 5. HTTP Action: POST request to JSONPlaceholder API
        print("\n⚡ [HTTP] Sending POST request to jsonplaceholder.typicode.com...")
        post_res = await manager.execute(
            "http_post", 
            {
                "url": "https://jsonplaceholder.typicode.com/posts",
                "json": {"name": "Mogesh", "profession": "Developer"}
            }
        )
        print(f"✅ POST Status: {post_res.get('status_code')}")
        print(f"📦 Response JSON: {post_res.get('json')}")

        # 6. HTTP Action: Download a file
        download_path = sandbox_dir / "downloaded_todo.json"
        print(f"\n⚡ [HTTP] Downloading todo item to sandbox/downloaded_todo.json...")
        dl_res = await manager.execute(
            "http_download", 
            {
                "url": "https://jsonplaceholder.typicode.com/todos/1",
                "dest_path": str(download_path)
            }
        )
        print(f"✅ Download Status: {dl_res.get('status')} (Code: {dl_res.get('status_code')})")

        # 7. HTTP Action: PUT request to JSONPlaceholder API
        print("\n⚡ [HTTP] Sending PUT request to jsonplaceholder.typicode.com...")
        put_res = await manager.execute(
            "http_put",
            {
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "json": {"id": 1, "title": "updated title", "body": "bar", "userId": 1}
            }
        )
        print(f"✅ PUT Status: {put_res.get('status_code')}")
        print(f"📦 Response JSON: {put_res.get('json')}")

        # 8. HTTP Action: PATCH request to JSONPlaceholder API
        print("\n⚡ [HTTP] Sending PATCH request to jsonplaceholder.typicode.com...")
        patch_res = await manager.execute(
            "http_patch",
            {
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "json": {"title": "patched title"}
            }
        )
        print(f"✅ PATCH Status: {patch_res.get('status_code')}")
        print(f"📦 Response JSON: {patch_res.get('json')}")

        # 9. HTTP Action: DELETE request to JSONPlaceholder API
        print("\n⚡ [HTTP] Sending DELETE request to jsonplaceholder.typicode.com...")
        delete_res = await manager.execute(
            "http_delete",
            {"url": "https://jsonplaceholder.typicode.com/posts/1"}
        )
        print(f"✅ DELETE Status: {delete_res.get('status_code')}")

        # 10. Filesystem Action: Create a log/report file
        print("\n📁 [Filesystem] Writing audit report to sandbox/report.txt...")
        report_content = (
            f"Execution Audit Log:\n"
            f"- Browser title: {nav_result.get('title')}\n"
            f"- HTTP GET code: {get_res.get('status_code')}\n"
            f"- HTTP POST response: {post_res.get('json')}\n"
            f"- HTTP PUT response title: {put_res.get('json', {}).get('title')}\n"
            f"- HTTP PATCH response title: {patch_res.get('json', {}).get('title')}\n"
            f"- HTTP DELETE status: {delete_res.get('status_code')}\n"
            f"- Downloaded file: {download_path.name}\n"
        )
        write_result = await manager.execute(
            "write_file", 
            {"path": "report.txt", "content": report_content}
        )
        print(f"✅ Bytes written: {write_result.get('bytes_written')}")
        
        # 11. Filesystem Action: Read the report file back
        print("📖 [Filesystem] Reading sandbox/report.txt content:")
        read_result = await manager.execute("read_file", {"path": "report.txt"})
        print("-" * 40)
        print(read_result.get("content"))
        print("-" * 40)
        
        # 9. Filesystem Action: List the directory files
        print("🗂️ [Filesystem] Listing files inside sandbox:")
        list_result = await manager.execute("list_dir", {"path": "."})
        for item in list_result.get("items", []):
            print(f"  - {item['name']} ({item['type']}, {item.get('size', 0)} bytes)")
            
    finally:
        # Always clean up providers
        print("\n🧹 Cleaning up browser and HTTP sessions...")
        await manager.close_providers()

if __name__ == "__main__":
    asyncio.run(main())
