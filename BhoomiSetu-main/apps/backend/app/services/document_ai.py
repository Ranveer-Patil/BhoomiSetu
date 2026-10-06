import base64
import io
import json
import re

import httpx
import pytesseract
from PIL import Image
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.intelligence import DocumentExtractedFields


def _parse_ocr_text(text: str) -> DocumentExtractedFields:
    def match(pattern: str) -> str | None:
        result = re.search(pattern, text, re.IGNORECASE)
        return result.group(1).strip() if result else None

    area_text = match(r"area(?:\s*\(ha\)|\s*hectares?)?\s*[:\-]\s*([0-9]+(?:\.[0-9]+)?)")
    owner = match(r"(?:owner|holder|name)\s*[:\-]\s*([^\n]+)")
    survey = match(r"(?:survey|khasra)(?:\s*(?:no|number|#))?\s*[:\-]\s*([A-Z0-9\-/]+)")
    date = match(r"(?:document\s*)?date\s*[:\-]\s*([0-9]{1,4}[\-/][0-9]{1,2}[\-/][0-9]{1,4})")
    document_type = match(r"document\s*type\s*[:\-]\s*([^\n]+)") or "Land ownership record"
    found = sum(value is not None for value in (owner, survey, area_text, date))
    return DocumentExtractedFields(
        owner_name=owner,
        khasra_survey_number=survey,
        area_hectares=float(area_text) if area_text else None,
        document_type=document_type,
        document_date=date,
        confidence=min(0.55 + found * 0.1, 0.9),
        extraction_method="tesseract_ocr",
        raw_text_excerpt=" ".join(text.split())[:500],
    )


async def _vision_extract(content: bytes, media_type: str) -> DocumentExtractedFields:
    schema = DocumentExtractedFields.model_json_schema()
    encoded = base64.b64encode(content).decode()
    prompt = (
        "Extract this Indian land record. Return only JSON matching this schema: "
        + json.dumps(schema)
    )
    payload = {
        "model": settings.openai_vision_model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                    },
                ],
            }
        ],
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )
        response.raise_for_status()
    parsed = json.loads(response.json()["choices"][0]["message"]["content"])
    parsed["extraction_method"] = "vision_llm"
    return DocumentExtractedFields.model_validate(parsed)


async def extract_document(content: bytes, media_type: str) -> DocumentExtractedFields:
    if settings.openai_api_key:
        try:
            return await _vision_extract(content, media_type)
        except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
            pass
    image = Image.open(io.BytesIO(content)).convert("RGB")
    text = await run_in_threadpool(
        pytesseract.image_to_string, image, lang="eng+mar+hin", timeout=45
    )
    return _parse_ocr_text(text)
