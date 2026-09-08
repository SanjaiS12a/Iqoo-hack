from app.ai import FallbackAIProvider
from app.content_ai import CompatibleContentProvider, FallbackContentProvider
from app.schemas import TutorReply


class FailingAI:
    def tutor(self, doubt: str):
        raise RuntimeError("provider unavailable")


class WorkingAI:
    def tutor(self, doubt: str):
        return TutorReply(concept_tag="fractions", response="Use a common denominator.")


class FailingContent:
    name = "openai"

    def extract(self, filename: str, media_type: str, content: bytes):
        raise RuntimeError("provider unavailable")


class WorkingContent:
    name = "gemini"

    def extract(self, filename: str, media_type: str, content: bytes):
        return {"provider": self.name}


def test_assessment_falls_back_to_next_provider():
    provider = FallbackAIProvider([("openai", FailingAI()), ("gemini", WorkingAI())])

    reply = provider.tutor("How do I add fractions?")

    assert reply.concept_tag == "fractions"
    assert provider.last_provider == "gemini"


def test_content_extraction_falls_back_to_next_provider():
    provider = FallbackContentProvider([FailingContent(), WorkingContent()])

    result = provider.extract("portion.pdf", "application/pdf", b"%PDF")

    assert result == {"provider": "gemini"}
    assert provider.last_provider == "gemini"
    assert provider.name == "gemini"


def test_unreadable_pdf_uses_scanned_document_prompt():
    text = CompatibleContentProvider._pdf_text("application/pdf", b"%PDF-1.4\nnot-a-complete-pdf")

    assert "appears scanned" in text
