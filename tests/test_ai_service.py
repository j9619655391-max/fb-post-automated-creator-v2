from app.services import ai_service
from app.services.ai_service import AIService


class FakeUsage:
    prompt_token_count = 10
    candidates_token_count = 20
    thoughts_token_count = 0
    cached_content_token_count = 0
    total_token_count = 30


class FakeResponse:
    text = '{"optimized_title": "Improved title", "optimized_body": "Improved body"}'
    usage_metadata = FakeUsage()


class FakeModels:
    def generate_content(self, model: str, contents: str):
        assert model == "gemini-2.5-flash"
        assert "new product launch" in contents
        return FakeResponse()


class FakeClient:
    models = FakeModels()

    def close(self):
        pass


def test_ai_optimization_with_mocked_provider(monkeypatch):
    monkeypatch.setattr(ai_service, "get_client", lambda: FakeClient())

    service = AIService()
    result = service.optimize_content("new product launch", "we are launching tomorrow")

    assert result == {
        "title": "Improved title",
        "body": "Improved body",
    }
