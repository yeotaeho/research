# 공고문 PDF 를 텍스트로 뽑는다 — 사용: uv run --no-project --with pypdf python -I pdf_text.py <PDF> [<출력 txt>]
import sys
from pypdf import PdfReader


def main() -> None:
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    reader = PdfReader(src)
    parts = []
    for i, page in enumerate(reader.pages, 1):
        parts.append(f"\n===== page {i} =====\n")
        parts.append(page.extract_text() or "")
    text = "".join(parts)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{src}: {len(reader.pages)} pages, {len(text)} chars -> {out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
