from textwrap import wrap


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    printable = [title, ""]
    for line in lines:
        printable.extend(wrap(str(line), width=92) or [""])
    pages = [printable[index:index + 48] for index in range(0, len(printable), 48)] or [[title]]
    font_id = 3 + len(pages) * 2
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (f"<< /Type /Pages /Count {len(pages)} /Kids [" + " ".join(
            f"{3 + index * 2} 0 R" for index in range(len(pages))
        ) + "] >>").encode("ascii"),
        font_id: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    for index, page_lines in enumerate(pages):
        page_id = 3 + index * 2
        stream_id = page_id + 1
        commands = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        for line in page_lines:
            safe = _escape(line.encode("latin-1", "replace").decode("latin-1"))
            commands.extend([f"({safe}) Tj", "T*"])
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {stream_id} 0 R >>"
        ).encode("ascii")
        objects[stream_id] = f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"

    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id in range(1, font_id + 1):
        offsets.append(len(document))
        document.extend(f"{object_id} 0 obj\n".encode("ascii"))
        document.extend(objects[object_id])
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {font_id + 1}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(f"trailer\n<< /Size {font_id + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(document)
