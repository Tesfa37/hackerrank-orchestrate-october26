# Free model access for the deletion-audit agent

The selected budget is $0 in billed API usage. The implemented provider is the Gemini Developer API Free Tier. Keep project billing disabled; no paid fallback is implemented. The organizer screenshot recommends an agent and scalability/robustness, but does not establish a mandatory API requirement.

1. Open https://aistudio.google.com/apikey and sign in to your Google account.
2. Complete any first-use terms yourself. Create or select a personal project that is on the Free Tier and has billing disabled. A new AI Studio account may create a default project and key during onboarding.
3. Create or view the Gemini API key for that free project. Check its model access and current rate limits in AI Studio. Start with `gemini-3.5-flash-lite` if the account makes it available.
4. Save the key only on your computer. For this checkout, create a root `.env` file with a line in the form `GEMINI_API_KEY=YOUR_KEY`. The root `.gitignore` excludes this file. The planned agent will load the value without printing it. It can instead read an existing `GEMINI_API_KEY` environment variable.
5. Tell the coding agent that the key is configured; do not send the key in chat. Before requests are run, confirm the project is still on the Free Tier and check the model's quota.

The user configured the local key. On October 24 the coding agent verified that `.env` exists, contains the required variable, and is ignored by Git, without displaying the key. The authenticated model lookup returned HTTP 200 for `gemini-3.5-flash-lite`. One minimal generation smoke test returned the expected `READY` response and used 6 input tokens plus 1 output token, 7 tokens total. Record this as development usage, separate from the eventual full-dataset run.

The restricted terminal could not resolve Google's API host, but the available Node runtime reached the API successfully. The submitted program must use ordinary documented Gemini API requests and must not depend on the coding-agent runtime. Model access and one generation are verified; account-specific remaining quota and end-to-end throughput are not yet measured. No key, account, project, or billing setting was created or changed by the coding agent.

The implementation groups short requests into ordinary synchronous calls, extracts media evidence once per request signature, caches repeat work, and records real token usage. Free-tier exhaustion stops the affected stage; it does not enable billing or switch to a paid model. The program does not inspect account billing and cannot enforce a dollar cap on an already billed project. The existing billing-disabled project must remain unchanged.

The earlier local `.env` verification above is historical. The cloud environment uses the existing injected credential. Fresh archive installation, no-cache preparation and offline replay are documented in [code/FRESH_ENVIRONMENT.md](../code/FRESH_ENVIRONMENT.md), with actual tests separated from live procedures in [archive_verification.md](../code/evaluation/archive_verification.md). Numeric quotas and current remaining availability were not rechecked during finalization; they depend on the project/model. No live no-cache regeneration was performed in that work.

Official references checked October 24, 2026:

- API keys: https://ai.google.dev/gemini-api/docs/api-key
- Pricing and free model availability: https://ai.google.dev/gemini-api/docs/pricing
- Free versus paid projects: https://ai.google.dev/gemini-api/docs/billing
- Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
