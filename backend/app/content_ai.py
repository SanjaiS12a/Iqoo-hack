import base64
import io
import json
from typing import Protocol

from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader


class ExtractedTopic(BaseModel):
    title: str
    learning_outcome: str
    sequence: int


class ExtractedQuestion(BaseModel):
    text: str
    expected_answer: str
    difficulty: str
    topic: str
    exam_weight: float = Field(ge=0, le=1)


class ExtractedPortion(BaseModel):
    title: str
    subject: str
    topics: list[ExtractedTopic]
    questions: list[ExtractedQuestion]


class ContentIntelligenceProvider(Protocol):
    name: str
    def extract(self, filename: str, media_type: str, content: bytes) -> ExtractedPortion: ...


class FallbackContentProvider:
    def __init__(self, providers: list[ContentIntelligenceProvider]):
        if not providers:
            raise ValueError("At least one content provider is required")
        self.providers = providers
        self.last_provider: str | None = None

    @property
    def name(self) -> str:
        return self.last_provider or "automatic"

    def extract(self, filename: str, media_type: str, content: bytes) -> ExtractedPortion:
        failures: list[str] = []
        for provider in self.providers:
            try:
                result = provider.extract(filename, media_type, content)
                self.last_provider = provider.name
                return result
            except Exception as error:
                failures.append(f"{provider.name}: {error.__class__.__name__}")
        raise RuntimeError(f"All content providers failed ({', '.join(failures)})")


class DemoContentProvider:
    name = "demo"

    def extract(self, filename: str, media_type: str, content: bytes) -> ExtractedPortion:
        lowered = filename.lower()
        if "fraction" in lowered:
            title = "Fractions and Rational Numbers"
            topics = [
                ExtractedTopic(title="Equivalent fractions", learning_outcome="Identify and construct equivalent fractions", sequence=1),
                ExtractedTopic(title="Adding fractions", learning_outcome="Add fractions using a common denominator", sequence=2),
                ExtractedTopic(title="Fraction word problems", learning_outcome="Model everyday quantities using fractions", sequence=3),
            ]
            subject = "Mathematics"
        else:
            title = "Current Classroom Portion"
            topics = [
                ExtractedTopic(title="Core concepts", learning_outcome="Explain the key ideas in the uploaded portion", sequence=1),
                ExtractedTopic(title="Guided application", learning_outcome="Apply the portion concepts to worked examples", sequence=2),
                ExtractedTopic(title="Independent practice", learning_outcome="Solve a new problem and explain the reasoning", sequence=3),
            ]
            subject = "General Studies"
        questions = [
            ExtractedQuestion(text=f"Explain one key idea from {topic.title}.", expected_answer=f"A clear explanation of {topic.title}", difficulty="Foundation" if index == 0 else "Core", topic=topic.title, exam_weight=max(.55, .85 - index * .1))
            for index, topic in enumerate(topics)
        ]
        return ExtractedPortion(title=title, subject=subject, topics=topics, questions=questions)


class CompatibleContentProvider:
    def __init__(self, name: str, api_key: str, model: str, base_url: str | None = None):
        self.name = name
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60, max_retries=2)

    def extract(self, filename: str, media_type: str, content: bytes) -> ExtractedPortion:
        prompt = (
            "Extract a school syllabus portion. Return JSON with title, subject, topics "
            "(title, learning_outcome, sequence) and questions (text, expected_answer, difficulty, topic, exam_weight 0..1). "
            "Create 3-8 topics and at least one question per topic. Do not invent official exam-frequency claims."
        )
        user_content: list[dict] = [{"type": "text", "text": f"Filename: {filename}\n{self._pdf_text(media_type, content)}"}]
        if media_type.startswith("image/"):
            encoded = base64.b64encode(content).decode("ascii")
            user_content.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{encoded}"}})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_content}],
            response_format={"type": "json_object"},
        )
        payload = response.choices[0].message.content
        if not payload:
            raise RuntimeError(f"{self.name} returned no extracted content")
        return ExtractedPortion.model_validate(json.loads(payload))

    @staticmethod
    def _pdf_text(media_type: str, content: bytes) -> str:
        if media_type != "application/pdf":
            return "Read the attached image."
        try:
            pages = PdfReader(io.BytesIO(content)).pages
            text = "\n".join((page.extract_text() or "") for page in pages)
        except Exception:
            text = ""
        return text[:30000] or "This PDF appears scanned; extract visible syllabus content conservatively."


def build_content_provider(settings) -> ContentIntelligenceProvider:
    if settings.ai_provider == "auto":
        providers: list[ContentIntelligenceProvider] = []
        if settings.openai_api_key:
            providers.append(CompatibleContentProvider("openai", settings.openai_api_key, settings.openai_model))
        if settings.gemini_api_key:
            providers.append(CompatibleContentProvider("gemini", settings.gemini_api_key, settings.gemini_model, "https://generativelanguage.googleapis.com/v1beta/openai/"))
        providers.append(DemoContentProvider())
        return FallbackContentProvider(providers)
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return CompatibleContentProvider("openai", settings.openai_api_key, settings.openai_model)
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return CompatibleContentProvider("gemini", settings.gemini_api_key, settings.gemini_model, "https://generativelanguage.googleapis.com/v1beta/openai/")
    if settings.ai_provider == "local":
        return CompatibleContentProvider("local", "local-model", settings.local_ai_model, settings.local_ai_base_url)
    return DemoContentProvider()
