"""PDF manipulation tools using the PdfProvider.

Each tool wraps a corresponding async method from the provider and defines an
input schema using Pydantic for validation.
"""

from typing import Any, List, Type

from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.pdf.provider import PdfProvider
from raavone_tools.exceptions import ProviderError, ExecutionError

# ---------------------------------------------------------------------
# Extract Text Tool
# ---------------------------------------------------------------------

class PdfExtractTextInput(BaseModel):
    """Input parameters for extracting text from a PDF.

    * ``pdf_path`` – Path to the PDF file.
    * ``pages`` – Optional list of page indices (0‑based). If omitted, all pages
      are processed.
    """

    pdf_path: str = Field(..., description="Path to the PDF file")
    pages: List[int] | None = Field(default=None, description="List of page indices to extract (0‑based).")


class PdfExtractTextTool(BaseTool[PdfProvider]):
    """Tool that extracts plain text from a PDF document."""

    name: str = "pdf_extract_text"
    description: str = "Extract text from a PDF file, optionally limited to specific pages."
    input_schema: Type[BaseModel] = PdfExtractTextInput

    async def execute(self, pdf_path: str, pages: List[int] | None = None) -> dict:
        if not self.provider:
            raise ProviderError("Pdf provider has not been assigned to this tool.")
        return await self.provider.extract_text(pdf_path, pages)

# ---------------------------------------------------------------------
# PDF Info Tool
# ---------------------------------------------------------------------

class PdfInfoInput(BaseModel):
    """Input for retrieving PDF metadata and page count."""

    pdf_path: str = Field(..., description="Path to the PDF file")


class PdfInfoTool(BaseTool[PdfProvider]):
    """Tool that returns basic PDF information such as page count and metadata."""

    name: str = "pdf_info"
    description: str = "Get PDF metadata, number of pages and other high‑level info."
    input_schema: Type[BaseModel] = PdfInfoInput

    async def execute(self, pdf_path: str) -> dict:
        if not self.provider:
            raise ProviderError("Pdf provider has not been assigned to this tool.")
        return await self.provider.info(pdf_path)

# ---------------------------------------------------------------------
# PDF Merge Tool
# ---------------------------------------------------------------------

class PdfMergeInput(BaseModel):
    """Input for merging multiple PDFs into a single output file."""

    pdf_paths: List[str] = Field(..., description="List of PDF file paths to merge (order preserved)")
    output_path: str = Field(..., description="Destination path for the merged PDF")


class PdfMergeTool(BaseTool[PdfProvider]):
    """Tool that merges several PDFs into one document."""

    name: str = "pdf_merge"
    description: str = "Merge multiple PDF files into a single PDF document."
    input_schema: Type[BaseModel] = PdfMergeInput

    async def execute(self, pdf_paths: List[str], output_path: str) -> dict:
        if not self.provider:
            raise ProviderError("Pdf provider has not been assigned to this tool.")
        return await self.provider.merge(pdf_paths, output_path)

# ---------------------------------------------------------------------
# PDF Split Tool
# ---------------------------------------------------------------------

class PdfSplitInput(BaseModel):
    """Input for splitting a PDF into separate page files."""

    pdf_path: str = Field(..., description="Path to the source PDF file")
    output_dir: str = Field(..., description="Directory where individual page PDFs will be stored")


class PdfSplitTool(BaseTool[PdfProvider]):
    """Tool that splits a PDF into single‑page PDFs."""

    name: str = "pdf_split"
    description: str = "Split a PDF into separate one‑page PDF files inside a directory."
    input_schema: Type[BaseModel] = PdfSplitInput

    async def execute(self, pdf_path: str, output_dir: str) -> dict:
        if not self.provider:
            raise ProviderError("Pdf provider has not been assigned to this tool.")
        return await self.provider.split(pdf_path, output_dir)

# ---------------------------------------------------------------------
# Images to PDF Tool
# ---------------------------------------------------------------------

class PdfImagesToPdfInput(BaseModel):
    """Input for converting a list of images into a single PDF document."""

    image_paths: List[str] = Field(..., description="List of image file paths to include in the PDF (ordered)")
    output_path: str = Field(..., description="Destination path for the generated PDF")


class PdfImagesToPdfTool(BaseTool[PdfProvider]):
    """Tool that creates a PDF from provided image files."""

    name: str = "pdf_images_to_pdf"
    description: str = "Combine multiple images into a single PDF document."
    input_schema: Type[BaseModel] = PdfImagesToPdfInput

    async def execute(self, image_paths: List[str], output_path: str) -> dict:
        if not self.provider:
            raise ProviderError("Pdf provider has not been assigned to this tool.")
        return await self.provider.images_to_pdf(image_paths, output_path)

# ---------------------------------------------------------------------
# Export list
# ---------------------------------------------------------------------

__all__ = [
    "PdfExtractTextTool",
    "PdfInfoTool",
    "PdfMergeTool",
    "PdfSplitTool",
    "PdfImagesToPdfTool",
]
