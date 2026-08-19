import os
import json
import asyncio
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.browser.tool import (
    NavigateTool,
    BackTool,
    ForwardTool,
    ReloadTool,
    ScreenshotTool,
    ScrollTool,
    ExtractTool,
    ClickTool,
    FillTool,
    TypeTool,
    PressTool,
    SelectTool,
    HoverTool,
    WaitTool,
    WaitForSelectorTool,
    GetAttributeTool,
    NewTabTool,
    ListTabsTool,
    SwitchTabTool,
    CloseTabTool,
    DownloadTool,
    UploadTool,
    GetCookiesTool,
    ClearCookiesTool,
)
from raavone_tools.filesystem.provider import FilesystemProvider
from raavone_tools.filesystem.tool import (
    WriteFileTool,
    ReadFileTool,
    ListDirTool,
    DeleteFileTool,
    CreateDirTool,
    CopyTool,
    MoveTool,
    ExistsTool,
    FileInfoTool,
    SearchTool,
)
from raavone_tools.http.provider import HttpProvider
from raavone_tools.http.tool import HttpGetTool, HttpPostTool, HttpDownloadTool
from raavone_tools.archive.provider import ArchiveProvider
from raavone_tools.archive.tool import CreateArchiveTool, ExtractArchiveTool, ListArchiveTool
from raavone_tools.git.provider import GitProvider
from raavone_tools.git.tool import GitStatusTool, GitLogTool
from raavone_tools.process.provider import ProcessProvider
from raavone_tools.process.tool import ProcessListTool, ProcessStartTool, ProcessStopTool, ProcessInfoTool
from raavone_tools.python.provider import PythonProvider
from raavone_tools.python.tool import PythonExecuteTool, PythonEnvInfoTool
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

# Global Manager and Loop
manager = ToolManager()
loop = asyncio.new_event_loop()


def run_async_loop(async_loop):
    asyncio.set_event_loop(async_loop)
    async_loop.run_forever()


async def init_manager():
    sandbox_dir = Path("./sandbox")
    sandbox_dir.mkdir(exist_ok=True)
    
    # 1. Setup Providers
    fs_provider = FilesystemProvider(workspace_root=sandbox_dir)
    browser_provider = BrowserProvider(headless=True)
    http_provider = HttpProvider()
    archive_provider = ArchiveProvider(workspace_root=sandbox_dir)
    git_provider = GitProvider(workspace_root=Path("."))
    process_provider = ProcessProvider()
    python_provider = PythonProvider(workspace_root=sandbox_dir)
    search_provider = SearchProvider()

    # 2. Register tools
    manager.register_tool(WriteFileTool(provider=fs_provider))
    manager.register_tool(ReadFileTool(provider=fs_provider))
    manager.register_tool(ListDirTool(provider=fs_provider))
    manager.register_tool(DeleteFileTool(provider=fs_provider))
    manager.register_tool(CreateDirTool(provider=fs_provider))
    manager.register_tool(CopyTool(provider=fs_provider))
    manager.register_tool(MoveTool(provider=fs_provider))
    manager.register_tool(ExistsTool(provider=fs_provider))
    manager.register_tool(FileInfoTool(provider=fs_provider))
    manager.register_tool(SearchTool(provider=fs_provider))
    
    manager.register_tool(NavigateTool(provider=browser_provider))
    manager.register_tool(BackTool(provider=browser_provider))
    manager.register_tool(ForwardTool(provider=browser_provider))
    manager.register_tool(ReloadTool(provider=browser_provider))
    manager.register_tool(ClickTool(provider=browser_provider))
    manager.register_tool(FillTool(provider=browser_provider))
    manager.register_tool(TypeTool(provider=browser_provider))
    manager.register_tool(PressTool(provider=browser_provider))
    manager.register_tool(SelectTool(provider=browser_provider))
    manager.register_tool(HoverTool(provider=browser_provider))
    manager.register_tool(WaitTool(provider=browser_provider))
    manager.register_tool(WaitForSelectorTool(provider=browser_provider))
    manager.register_tool(GetAttributeTool(provider=browser_provider))
    manager.register_tool(NewTabTool(provider=browser_provider))
    manager.register_tool(ListTabsTool(provider=browser_provider))
    manager.register_tool(SwitchTabTool(provider=browser_provider))
    manager.register_tool(CloseTabTool(provider=browser_provider))
    manager.register_tool(DownloadTool(provider=browser_provider))
    manager.register_tool(UploadTool(provider=browser_provider))
    manager.register_tool(GetCookiesTool(provider=browser_provider))
    manager.register_tool(ClearCookiesTool(provider=browser_provider))
    manager.register_tool(ScreenshotTool(provider=browser_provider))
    manager.register_tool(ScrollTool(provider=browser_provider))
    manager.register_tool(ExtractTool(provider=browser_provider))
    
    manager.register_tool(HttpGetTool(provider=http_provider))
    manager.register_tool(HttpPostTool(provider=http_provider))
    manager.register_tool(HttpDownloadTool(provider=http_provider))
    
    manager.register_tool(CreateArchiveTool(provider=archive_provider))
    manager.register_tool(ExtractArchiveTool(provider=archive_provider))
    manager.register_tool(ListArchiveTool(provider=archive_provider))
    
    manager.register_tool(GitStatusTool(provider=git_provider))
    manager.register_tool(GitLogTool(provider=git_provider))
    
    manager.register_tool(ProcessListTool(provider=process_provider))
    manager.register_tool(ProcessStartTool(provider=process_provider))
    manager.register_tool(ProcessStopTool(provider=process_provider))
    manager.register_tool(ProcessInfoTool(provider=process_provider))
    
    manager.register_tool(PythonExecuteTool(provider=python_provider))
    manager.register_tool(PythonEnvInfoTool(provider=python_provider))
    
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

    await manager.initialize_providers()
    print("✅ All providers successfully initialized in async background thread.")


class DashboardHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Redirect default static file requests to the static folder
        root = Path(__file__).parent / "static"
        requested = path.lstrip("/")
        if requested == "" or requested == "/":
            requested = "index.html"
        return str(root / requested)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            tool_list = list(manager.tools.keys())
            self.wfile.write(json.dumps({
                "status": "online",
                "registered_tools": tool_list
            }).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/execute":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode("utf-8"))
                tool_name = data.get("tool")
                arguments = data.get("arguments", {})
                
                # Execute in async thread pool
                future = asyncio.run_coroutine_threadsafe(
                    manager.execute(tool_name, arguments),
                    loop
                )
                result = future.result()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "result": result}).encode("utf-8"))
                
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("🚀 RaavOne Tools GUI Server running on http://localhost:8000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping loop...")
        loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    # Start loop on background thread
    t = threading.Thread(target=run_async_loop, args=(loop,), daemon=True)
    t.start()
    
    # Initialize providers inside the loop
    asyncio.run_coroutine_threadsafe(init_manager(), loop).result()
    
    # Run the HTTP server on the main thread
    run_server()
