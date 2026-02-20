import base64
import io
import os
from typing import List

from pdf2image import convert_from_bytes

from openai import OpenAI


def _images_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 6) -> List[bytes]:
    """Convert first max_pages of a PDF (bytes) to PNG image bytes."""
    # Use a moderate DPI and only render the first max_pages to
    # keep OCR reasonably fast even for large PDFs.
    images = convert_from_bytes(
        pdf_bytes,
        fmt="png",
        dpi=150,
        first_page=1,
        last_page=max_pages,
    )
    png_bytes_list: List[bytes] = []

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes_list.append(buf.getvalue())

    return png_bytes_list


def _extract_text_from_image_bytes(client: OpenAI, image_bytes: bytes) -> str:
    """Use OpenAI vision model to extract textual content from a single page image."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = (
        "You are an OCR tool for ReCOGnAIze cognitive assessment reports. "
        "Given an image of a report page, extract ALL visible text as plain text. "
        "Preserve section titles, domain names, numeric scores, and labels like WEAK, AVERAGE, STRONG. "
        "Do not summarize or interpret. Just return the raw text you see in reading order."
    )

    user_instruction = (
        "Extract all visible text from this report page. "
        "Include all numbers, percentiles, and score labels."
    )

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_instruction},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}",
                        },
                    },
                ],
            },
        ],
        max_tokens=1200,
    )

    return (response.choices[0].message.content or "").strip()


def extract_text_from_pdf_with_vision(pdf_bytes: bytes, max_pages: int = 6) -> str:
    """Use OpenAI vision to OCR up to max_pages from a PDF and return concatenated text.

    This is used as a fallback when PyPDF2 cannot extract meaningful text
    (e.g., for non-highlightable / scanned PDFs).
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    page_images = _images_from_pdf_bytes(pdf_bytes, max_pages=max_pages)
    all_pages_text: List[str] = []

    for page_index, img_bytes in enumerate(page_images, start=1):
        try:
            page_text = _extract_text_from_image_bytes(client, img_bytes)
        except Exception as e:
            page_text = f"[OCR error on page {page_index}: {e}]"
        if page_text:
            all_pages_text.append(f"--- OCR Page {page_index} ---\n{page_text}")

    return "\n\n".join(all_pages_text)
