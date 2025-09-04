import pytest
from pathlib import Path
from src.rag_system.document_service import DocumentService
from src.rag_system.schemas import FileType
import pandas as pd

def test_process_text(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello, this is a test document.")

    service = DocumentService()
    docs, meta = service.process_single_file(str(file_path), FileType.TXT)

    assert len(docs) > 0
    assert "Hello" in docs[0].page_content
    assert meta["characters"] == len("Hello, this is a test document.")

def test_process_csv(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id,name\n1,John\n2,Alice")

    service = DocumentService()
    docs, meta = service.process_single_file(str(file_path), FileType.CSV)

    assert len(docs) > 0
    assert meta["rows"] == 2
    assert "John" in docs[0].page_content

def test_process_pdf(pdf_sample_path):
    service = DocumentService()
    docs, meta = service.process_single_file(pdf_sample_path, FileType.PDF)

    assert isinstance(docs, list)
    assert "Page" in docs[0].page_content

from PIL import Image

def test_process_image(tmp_path):
    # Create a dummy image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(img_path)

    service = DocumentService()
    docs, meta = service.process_single_file(str(img_path), FileType.IMAGE)

    assert len(docs) == 1
    assert "Image:" in docs[0].page_content
    assert meta["has_images"] is True
    assert meta["extracted_images"] == 1


def test_process_excel(tmp_path):
    # Create a dummy Excel file with 2 sheets
    excel_path = tmp_path / "sample.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame({"id": [1, 2], "value": [10, 20]}).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]}).to_excel(writer, sheet_name="Sheet2", index=False)

    service = DocumentService()
    docs, meta = service.process_single_file(str(excel_path), FileType.XLSX)

    assert len(docs) >= 2   # At least one doc per sheet
    assert "Excel Sheet: Sheet1" in docs[0].page_content
    assert meta["sheets"] == 2
    assert meta["total_rows"] == 4  # 2 rows per sheet
