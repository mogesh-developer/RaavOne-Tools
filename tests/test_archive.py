import os
import tempfile
import zipfile
import pytest
from pathlib import Path

from raavone_tools.manager import ToolManager
from raavone_tools.archive.provider import ArchiveProvider
from raavone_tools.archive.tool import CreateArchiveTool, ExtractArchiveTool, ListArchiveTool
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


@pytest.mark.asyncio
async def test_archive_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        manager = ToolManager()
        provider = ArchiveProvider(workspace_root=workspace_root)
        
        manager.register_tool(CreateArchiveTool(provider=provider))
        manager.register_tool(ExtractArchiveTool(provider=provider))
        manager.register_tool(ListArchiveTool(provider=provider))
        
        await manager.initialize_providers()
        
        try:
            # 1. Setup sample directory to archive
            src_dir = workspace_root / "project"
            src_dir.mkdir()
            (src_dir / "file1.txt").write_text("Hello One")
            (src_dir / "file2.txt").write_text("Hello Two")
            
            # Archive destination path
            archive_path = "project.zip"
            
            # 2. Test create archive
            res_create = await manager.execute(
                "archive_create",
                {"source_path": "project", "archive_path": archive_path}
            )
            assert res_create["status"] == "success"
            assert os.path.exists(workspace_root / archive_path)
            
            # 3. Test list archive
            res_list = await manager.execute(
                "archive_list",
                {"archive_path": archive_path}
            )
            assert res_list["status"] == "success"
            assert res_list["count"] == 2
            filenames = {f["filename"] for f in res_list["files"]}
            assert "file1.txt" in filenames
            assert "file2.txt" in filenames
            
            # 4. Test extract archive
            extract_dest = "extracted_project"
            res_extract = await manager.execute(
                "archive_extract",
                {"archive_path": archive_path, "dest_path": extract_dest}
            )
            assert res_extract["status"] == "success"
            assert os.path.exists(workspace_root / extract_dest / "file1.txt")
            assert (workspace_root / extract_dest / "file1.txt").read_text() == "Hello One"
            
            # 5. Security Check: Path outside workspace root
            with pytest.raises(ExecutionError) as exc_info:
                await manager.execute(
                    "archive_create",
                    {"source_path": "project", "archive_path": "../outside.zip"}
                )
            assert "Security Validation Error" in str(exc_info.value)
                
            # 6. Security Check: Extract malicious path (Zip Slip)
            malicious_zip = workspace_root / "malicious.zip"
            with zipfile.ZipFile(malicious_zip, "w") as mzip:
                # Add a file named with path traversal
                mzip.writestr("../traversal.txt", "Malicious content")
                
            with pytest.raises(ExecutionError) as exc_info2:
                await manager.execute(
                    "archive_extract",
                    {"archive_path": "malicious.zip", "dest_path": "safe_dir"}
                )
            assert "Security boundary breach" in str(exc_info2.value)

        finally:
            await manager.close_providers()
