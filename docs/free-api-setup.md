# Free model access for the deletion-audit agent

The selected budget is $0 in billed API usage. The proposed provider is the Gemini Developer API Free Tier. Keep project billing disabled; no paid fallback is planned.

1. Open https://aistudio.google.com/apikey and sign in to your Google account.
2. Complete any first-use terms yourself. Create or select a personal project that is on the Free Tier and has billing disabled. A new AI Studio account may create a default project and key during onboarding.
3. Create or view the Gemini API key for that free project. Check its model access and current rate limits in AI Studio. Start with `gemini-3.5-flash-lite` if the account makes it available.
4. Save the key only on your computer. For this checkout, create a root `.env` file with a line in the form `GEMINI_API_KEY=YOUR_KEY`. The root `.gitignore` excludes this file. The planned agent will load the value without printing it. It can instead read an existing `GEMINI_API_KEY` environment variable.
5. Tell the coding agent that the key is configured; do not send the key in chat. Before requests are run, confirm the project is still on the Free Tier and check the model's quota.

No key, account, project, or billing setting was created or changed by the coding agent during planning. No model calls have been made. The runtime implementation is still pending, so access and throughput have not been tested.

The implementation will group short requests into ordinary synchronous calls, extract image evidence once, cache repeat work, and record real token usage. Free-tier exhaustion pauses the affected stage; it does not enable billing or switch to a paid model.

Official references checked October 24, 2026:

- API keys: https://ai.google.dev/gemini-api/docs/api-key
- Pricing and free model availability: https://ai.google.dev/gemini-api/docs/pricing
- Free versus paid projects: https://ai.google.dev/gemini-api/docs/billing
- Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
