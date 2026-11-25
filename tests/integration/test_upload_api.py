"""Integration tests for transient document uploads."""

from io import BytesIO
from zipfile import ZipFile


def _docx_bytes(text: str) -> bytes:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>'
        + text
        + '</w:t></w:r></w:p></w:body></w:document>'
    ).encode("utf-8")
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return output.getvalue()


def test_extract_text_document(client):
    response = client.post(
        "/api/v1/extract",
        data={"file": (BytesIO(b"A draft from a text file."), "draft.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["text"] == "A draft from a text file."


def test_extract_docx_document(client):
    response = client.post(
        "/api/v1/extract",
        data={"file": (BytesIO(_docx_bytes("A DOCX draft.")), "draft.docx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["text"] == "A DOCX draft."


def test_reject_unsupported_upload(client):
    response = client.post(
        "/api/v1/extract",
        data={"file": (BytesIO(b"not an executable"), "draft.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "DocumentExtractionError"


def test_reject_empty_upload(client):
    response = client.post(
        "/api/v1/extract",
        data={"file": (BytesIO(b""), "empty.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "DocumentExtractionError"
