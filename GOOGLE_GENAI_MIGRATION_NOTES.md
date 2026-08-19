# Google GenAI Migration Notes

## Official references

1. [Google Gen AI Python SDK documentation](https://googleapis.github.io/python-genai/)

   The supported Python package is `google-genai`, imported as `from google import genai`. The Gemini Developer API client is created with `genai.Client(api_key=...)`, and text generation uses `client.models.generate_content(model=..., contents=...)`. The sync client exposes `close()` for cleanup.

2. [Gemini token usage documentation](https://ai.google.dev/gemini-api/docs/generate-content/tokens)

   A generation response exposes `usage_metadata` with `prompt_token_count`, `candidates_token_count`, `thoughts_token_count`, `cached_content_token_count`, and `total_token_count` (Python SDK snake_case equivalents). Input and output token counts are used for cost calculation.

3. [Gemini Generate Content API reference](https://ai.google.dev/api/generate-content)

   The official Python examples use `from google import genai`, `client.models.generate_content`, and `response.text`. The API supports structured generation configuration, safety settings, and the `GenerateContentResponse` usage metadata.

4. [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)

   Pricing is model- and tier-dependent. The implementation therefore stores the input/output rates alongside each usage record and exposes environment-configurable defaults for the selected `gemini-2.5-flash` model. Current defaults are $0.30 per million input tokens and $2.50 per million output/thought tokens; operators should update settings when Google changes pricing or the deployment uses a different tier/model.

## Implementation decisions

The project now centralizes client creation, usage extraction, and estimated USD cost calculation in `app/services/genai_client.py`. Generation and optimization calls persist usage rows in `content_generation_usage`, linked to `content_generation_jobs`. Provider failures and malformed responses still preserve job status and, when available, usage metadata.
