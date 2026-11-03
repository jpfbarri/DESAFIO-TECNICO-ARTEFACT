import json
import re
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

DEFAULT_POLICIES_JSON_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "policies_sections.json"
)
DEFAULT_POLICIES_PDF_PATH = (
    Path(__file__).resolve().parent.parent.parent / "arquivos" / "políticas_da_loja.pdf"
)
SECTION_HEADING_PATTERN = re.compile(r"\n(?=\d{1,2}\.\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ])")


class PolicySection(BaseModel):
    section_id: str = Field(..., description="Identificador numérico da seção do manual")
    title: str = Field(..., description="Título da seção")
    page: int = Field(default=1, ge=1, description="Página inicial da seção no PDF")
    tags: List[str] = Field(default_factory=list, description="Palavras-chave semânticas da seção")
    content: str = Field(..., min_length=10, description="Conteúdo integral da seção")


def load_policy_sections(
    json_path: Path = DEFAULT_POLICIES_JSON_PATH,
    pdf_path: Path = DEFAULT_POLICIES_PDF_PATH,
) -> List[PolicySection]:
    if json_path.exists():
        return _load_sections_from_json(json_path)
    if pdf_path.exists():
        return _extract_sections_from_pdf(pdf_path)
    raise FileNotFoundError(f"Manual de políticas não encontrado em {json_path} ou {pdf_path}")


def _load_sections_from_json(json_path: Path) -> List[PolicySection]:
    raw_records = json.loads(json_path.read_text(encoding="utf-8"))
    return [PolicySection(**record) for record in raw_records]


def _extract_sections_from_pdf(pdf_path: Path) -> List[PolicySection]:
    import pypdf

    reader = pypdf.PdfReader(str(pdf_path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    raw_chunks = SECTION_HEADING_PATTERN.split(full_text)
    sections: List[PolicySection] = []
    for index, chunk in enumerate(raw_chunks, start=1):
        cleaned_chunk = chunk.strip()
        if not cleaned_chunk:
            continue
        first_line = cleaned_chunk.splitlines()[0].strip()
        sections.append(
            PolicySection(
                section_id=str(index),
                title=first_line,
                page=1,
                tags=[],
                content=cleaned_chunk,
            )
        )
    return sections

