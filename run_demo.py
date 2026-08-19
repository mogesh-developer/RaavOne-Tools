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
from raavone_tools.archive.provider import ArchiveProvider
from raavone_tools.archive.tool import CreateArchiveTool, ExtractArchiveTool, ListArchiveTool
from raavone_tools.git.provider import GitProvider
from raavone_tools.git.tool import GitStatusTool, GitLogTool
from raavone_tools.process.provider import ProcessProvider
from raavone_tools.process.tool import ProcessListTool, ProcessStartTool, ProcessStopTool, ProcessInfoTool
from raavone_tools.python.provider import PythonProvider
from raavone_tools.python.tool import PythonExecuteTool, PythonRunFileTool, PythonEnvInfoTool
from raavone_tools.search.provider import SearchProvider
from raavone_tools.search.tool import WebSearchTool
from raavone_tools.database.provider import BaseDatabaseProvider, SQLiteProvider
from raavone_tools.database.tool import DbQueryTool, DbExecuteTool, DbTablesTool, DbSchemaTool
from raavone_tools.docker.provider import DockerProvider
from raavone_tools.docker.tool import (
    DockerListContainersTool,
    DockerStartContainerTool,
    DockerStopContainerTool,
    DockerRestartContainerTool,
    DockerContainerLogsTool,
    DockerListImagesTool,
)

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
    
    # Register Archive tools
    archive_provider = ArchiveProvider(workspace_root=sandbox_dir)
    manager.register_tool(CreateArchiveTool(provider=archive_provider))
    manager.register_tool(ExtractArchiveTool(provider=archive_provider))
    manager.register_tool(ListArchiveTool(provider=archive_provider))
    
    # Register Git tools
    git_provider = GitProvider(workspace_root=Path("."))
    manager.register_tool(GitStatusTool(provider=git_provider))
    manager.register_tool(GitLogTool(provider=git_provider))
    
    # Register Process tools
    process_provider = ProcessProvider()
    manager.register_tool(ProcessListTool(provider=process_provider))
    manager.register_tool(ProcessStartTool(provider=process_provider))
    manager.register_tool(ProcessStopTool(provider=process_provider))
    manager.register_tool(ProcessInfoTool(provider=process_provider))
    
    # Register Python tools
    python_provider = PythonProvider(workspace_root=sandbox_dir)
    manager.register_tool(PythonExecuteTool(provider=python_provider))
    manager.register_tool(PythonRunFileTool(provider=python_provider))
    manager.register_tool(PythonEnvInfoTool(provider=python_provider))
    
    # Register Search tools
    search_provider = SearchProvider()
    manager.register_tool(WebSearchTool(provider=search_provider))
    
    # Register Database tools
    database_provider = SQLiteProvider(workspace_root=sandbox_dir, db_path="demo.db")
    manager.register_tool(DbQueryTool(provider=database_provider))
    manager.register_tool(DbExecuteTool(provider=database_provider))
    manager.register_tool(DbTablesTool(provider=database_provider))
    manager.register_tool(DbSchemaTool(provider=database_provider))
    
    # Register Docker tools
    docker_provider = DockerProvider()
    manager.register_tool(DockerListContainersTool(provider=docker_provider))
    manager.register_tool(DockerStartContainerTool(provider=docker_provider))
    manager.register_tool(DockerStopContainerTool(provider=docker_provider))
    manager.register_tool(DockerRestartContainerTool(provider=docker_provider))
    manager.register_tool(DockerContainerLogsTool(provider=docker_provider))
    manager.register_tool(DockerListImagesTool(provider=docker_provider))
    
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

        # 9a. Archive Action: Create a folder and compress it
        print("\n📦 [Archive] Preparing files for archiving...")
        await manager.execute("write_file", {"path": "project_to_zip/file1.txt", "content": "File 1 details"})
        await manager.execute("write_file", {"path": "project_to_zip/file2.txt", "content": "File 2 details"})
        
        print("📦 [Archive] Creating ZIP archive from 'project_to_zip'...")
        await manager.execute(
            "archive_create",
            {"source_path": "project_to_zip", "archive_path": "project.zip"}
        )
        print("✅ ZIP archive created: project.zip")

        # 9b. Archive Action: List contents of ZIP archive
        print("📦 [Archive] Listing files in project.zip...")
        list_zip = await manager.execute("archive_list", {"archive_path": "project.zip"})
        for file in list_zip.get("files", []):
            print(f"  - {file['filename']} ({file['file_size']} bytes)")

        # 9c. Archive Action: Extract contents to another folder
        print("📦 [Archive] Extracting project.zip to 'extracted_demo'...")
        await manager.execute(
            "archive_extract",
            {"archive_path": "project.zip", "dest_path": "extracted_demo"}
        )
        print("✅ ZIP extracted successfully to 'extracted_demo'")

        # 9d. Git Action: Get status and log details
        print("\n🐙 [Git] Fetching repository status...")
        git_status_res = await manager.execute("git_status", {})
        print(f"✅ Current Branch: {git_status_res.get('branch')}")
        print(f"📦 Modified files count: {len(git_status_res.get('modified', []))}")
        print(f"📦 Untracked files count: {len(git_status_res.get('untracked', []))}")

        print("\n🐙 [Git] Fetching last 3 commits...")
        git_log_res = await manager.execute("git_log", {"limit": 3})
        for commit in git_log_res.get("commits", []):
            print(f"  - [{commit['hash'][:7]}] {commit['message']} ({commit['author']} on {commit['date']})")

        # 9e. Process Action: Start background task and monitor
        print("\n⚙️ [Process] Spawning background task...")
        bg_proc = await manager.execute("process_start", {"command": 'python -c "import time; time.sleep(15)"'})
        bg_pid = bg_proc.get("pid")
        print(f"✅ Process started successfully with PID: {bg_pid}")

        print("⚙️ [Process] Fetching details for spawned PID...")
        proc_info_res = await manager.execute("process_info", {"pid": bg_pid})
        print(f"✅ Active state: {proc_info_res.get('status_state')} | Memory RSS: {proc_info_res.get('rss_bytes')} bytes")

        print("⚙️ [Process] Querying system for python processes...")
        proc_list_res = await manager.execute("process_list", {"name_filter": "python", "limit": 3})
        for p in proc_list_res.get("processes", []):
            print(f"  - PID {p['pid']}: {p['name']} ({p['status']})")

        print("⚙️ [Process] Stopping spawned process...")
        await manager.execute("process_stop", {"pid": bg_pid})
        print("✅ Process stopped successfully.")

        # 9f. Python Action: Execute inline calculation and logic
        print("\n🐍 [Python] Running PythonExecuteTool...")
        calc_code = (
            "import json\n"
            "numbers = [10, 20, 30, 40, 50]\n"
            "avg = sum(numbers) / len(numbers)\n"
            "print(json.dumps({'average': avg, 'status': 'calculated'}))"
        )
        python_res = await manager.execute("python_execute", {"code": calc_code})
        print(f"✅ Python Exit Code: {python_res.get('exit_code')}")
        print(f"📦 Python stdout: {python_res.get('stdout')}")

        # 9g. Python Action: Get environment stats
        print("\n🐍 [Python] Fetching python environment details...")
        env_res = await manager.execute("python_env_info", {})
        print(f"✅ Python Version: {env_res.get('python_version').splitlines()[0]}")
        print(f"📦 Installed packages count: {len(env_res.get('installed_packages', {}))}")

        # 9h. Search Action: Query search engine
        print("\n🔎 [Search] Querying web search for 'Python latest news'...")
        search_res = await manager.execute("web_search", {"query": "Python latest news", "max_results": 2})
        print(f"✅ Search Status: {search_res.get('status')}")
        for idx, result in enumerate(search_res.get("results", [])):
            print(f"  Result {idx+1}: {result.get('title')} ({result.get('url')})")

        # 9i. Database Action: Initialize and query SQLite database
        print("\n🗄️ [Database] Creating sqlite database and projects table...")
        await manager.execute("db_execute", {
            "sql": "CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, category TEXT);"
        })
        await manager.execute("db_execute", {
            "sql": "INSERT INTO projects (name, category) VALUES (?, ?);",
            "params": ["RaavOne Tools", "Agent Framework"]
        })
        
        print("🗄️ [Database] Querying projects table...")
        db_query_res = await manager.execute("db_query", {
            "sql": "SELECT * FROM projects LIMIT 5;"
        })
        for row in db_query_res.get("rows", []):
            print(f"  - Project {row['id']}: {row['name']} ({row['category']})")

        # 9j. Docker Action: List containers and images (handled safely if offline)
        print("\n🐳 [Docker] Fetching local docker containers and images...")
        try:
            docker_list_res = await manager.execute("docker_list_containers", {"all_containers": True})
            print(f"✅ Docker Status: success")
            print(f"📦 Containers found: {docker_list_res.get('count')}")
            for container in docker_list_res.get("containers", [])[:3]:
                print(f"  - Container: {container.get('name')} | Status: {container.get('status')} | Image: {container.get('image')}")
            
            images_res = await manager.execute("docker_list_images", {})
            print(f"📦 Local images count: {images_res.get('count')}")
        except Exception as e:
            print(f"⚠️ Docker check skipped (daemon likely offline or not installed): {e}")

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
