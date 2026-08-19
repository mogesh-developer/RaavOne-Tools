"""PDF provider implementing PDF manipulation using pypdf library.

The provider offers basic functionalities: extracting text, retrieving metadata,
merging multiple PDFs, splitting a PDF into individual pages, and converting
images to a PDF document.
"""

from typing import Any, Dict, List, Optional

import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ExecutionError, ProviderError


class PdfProvider(BaseProvider):
    """Provider for PDF operations using pypdf.

    All methods raise ``ExecutionError`` on failure and perform basic
    validation of input paths to stay within the workspace.
    """

    def _validate_path(self, path: str) -> Path:
        p = Path(path).expanduser().resolve()
        # Simple workspace guard – ensure the path is under the project root.
        project_root = Path("d:/raavone-tools").resolve()
        if not str(p).startswith(str(project_root)):
            raise ProviderError(f"Path {p} is outside the allowed workspace.")
        return p

    # ---------------------------------------------------------------------
    # Text extraction
    # ---------------------------------------------------------------------
    async def extract_text(self, pdf_path: str, pages: Optional[List[int]] = None) -> Dict[str, Any]:
        path = self._validate_path(pdf_path)
        try:
            reader = PdfReader(str(path))
            if pages is None:
                pages = list(range(len(reader.pages)))
            text_parts = []
            for idx in pages:
                if idx < 0 or idx >= len(reader.pages):
                    raise ExecutionError(f"Page index {idx} out of range for {pdf_path}.")
                text_parts.append(reader.pages[idx].extract_text() or "")
            return {"status": "success", "text": "\n".join(text_parts)}
        except Exception as e:
            raise ExecutionError(f"Failed to extract text from {pdf_path}: {e}") from e

    # ---------------------------------------------------------------------
    # PDF metadata/info
    # ---------------------------------------------------------------------
    async def info(self, pdf_path: str) -> Dict[str, Any]:
        path = self._validate_path(pdf_path)
        try:
            reader = PdfReader(str(path))
            info = reader.metadata
            return {
                "status": "success",
                "pages": len(reader.pages),
                "metadata": {k: str(v) for k, v in info.items()} if info else {},
            }
        except Exception as e:
            raise ExecutionError(f"Failed to read info from {pdf_path}: {e}") from e

    # ---------------------------------------------------------------------
    # Merge PDFs
    # ---------------------------------------------------------------------
    async def merge(self, pdf_paths: List[str], output_path: str) -> Dict[str, Any]:
        out_path = self._validate_path(output_path)
        writer = PdfWriter()
        try:
            for p in pdf_paths:
                src = self._validate_path(p)
                reader = PdfReader(str(src))
                for page in reader.pages:
                    writer.add_page(page)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                writer.write(f)
            return {"status": "success", "output": str(out_path)}
        except Exception as e:
            raise ExecutionError(f"Failed to merge PDFs: {e}") from e

    # ---------------------------------------------------------------------
    # Split PDF into individual pages
    # ---------------------------------------------------------------------
    async def split(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        src_path = self._validate_path(pdf_path)
        out_dir = self._validate_path(output_dir)
        try:
            reader = PdfReader(str(src_path))
            out_dir.mkdir(parents=True, exist_ok=True)
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                out_file = out_dir / f"page_{i}.pdf"
                with open(out_file, "wb") as f:
                    writer.write(f)
            return {"status": "success", "directory": str(out_dir), "pages": len(reader.pages)}
        except Exception as e:
            raise ExecutionError(f"Failed to split PDF {pdf_path}: {e}") from e

    # ---------------------------------------------------------------------
    # Convert images to a single PDF document
    # ---------------------------------------------------------------------
    async def images_to_pdf(self, image_paths: List[str], output_path: str) -> Dict[str, Any]:
        out_path = self._validate_path(output_path)
        writer = PdfWriter()
        try:
            from PIL import Image

            for img_path in image_paths:
                img_file = self._validate_path(img_path)
                img = Image.open(str(img_file)).convert("RGB")
                # Save to temporary PDF page then add
                temp_pdf = Path(img_file).with_suffix(".pdf")
                img.save(temp_pdf, "PDF", resolution=100.0)
                page_reader = PdfReader(str(temp_pdf))
                writer.add_page(page_reader.pages[0])
                temp_pdf.unlink(missing_ok=True)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                writer.write(f)
            return {"status": "success", "output": str(out_path)}
        except Exception as e:
            raise ExecutionError(f"Failed to create PDF from images: {e}") from e

    async def close(self) -> None:
        # No persistent resources to clean up for pypdf.
        pass
