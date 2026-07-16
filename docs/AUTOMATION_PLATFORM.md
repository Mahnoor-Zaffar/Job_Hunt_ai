# Browser Automation Platform

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                   AutoApplyWorkflow                      │
│  (ATS-specific config: field mappings, selectors, URLs)  │
└──────────────────────┬───────────────────────────────────┘
                       │ uses
┌──────────────────────▼───────────────────────────────────┐
│                   WorkflowEngine                         │
│  (step pipeline: navigate → fill → upload → submit)     │
└──────────────────────┬───────────────────────────────────┘
                       │ executes
┌──────────────────────▼───────────────────────────────────┐
│                   Action Executor                        │
│  (navigate, click, fill, type, upload, extract, wait)   │
└──────────────────────┬───────────────────────────────────┘
                       │ operates
┌──────────────────────▼───────────────────────────────────┐
│                   AutomationBrowser                      │
│  (ContextPool → PagePool → CookieManager → AuthManager)  │
└──────────────────────┬───────────────────────────────────┘
                       │ drives
┌──────────────────────▼───────────────────────────────────┐
│                      Playwright                          │
│                   (Chromium browser)                      │
└──────────────────────────────────────────────────────────┘

Support services:
  RecoveryEngine  →  exponential backoff retry
  EventBus        →  step lifecycle events
  Metrics         →  duration, success rate logging
```

## Components

### AutomationBrowser

Enhanced browser manager with resource pooling.

| Feature | Description |
|---|---|
| ContextPool | Up to 5 concurrent browser contexts |
| PagePool | Reusable pages within contexts |
| CookieManager | Save/load cookies per session |
| AuthManager | Persist auth state per platform |
| Downloads | Configurable download directory |
| Screenshots | Full-page capture at any step |

### WorkflowEngine

Composable step pipeline. Each step is a standalone async function.
Steps run sequentially; failure in any step stops the workflow.

Pre-built steps:
- `step_navigate` — navigate to URL
- `step_wait` — wait for selector
- `step_click` — click element
- `step_fill` — fill input field
- `step_upload` — upload file
- `step_extract` — extract text
- `step_screenshot` — capture screenshot

### Action Executor

Reusable Playwright interaction functions:

| Action | Description |
|---|---|
| `navigate(page, url)` | Navigate to URL |
| `click(page, selector)` | Click element |
| `type_text(page, selector, text)` | Type with human delay |
| `fill_field(page, selector, value)` | Fill input |
| `select_option(page, selector, value)` | Select dropdown |
| `upload_file(page, selector, path)` | Upload file |
| `extract_text(page, selector)` | Get text content |
| `extract_form_fields(page)` | Detect all form fields |
| `human_delay()` | Random delay (200-800ms) |

### Recovery Engine

Exponential backoff for transient failures.

```python
from backend.automation import with_recovery, RecoveryConfig

result = await with_recovery(
    my_async_fn, arg1, arg2,
    recovery=RecoveryConfig(max_retries=3, base_delay_seconds=1.0),
    on_retry=lambda attempt, error: print(f"Retry {attempt}: {error}"),
)
```

### AutoApplyWorkflow

Pre-built workflow for automated job applications.

```python
from backend.automation import AutoApplyWorkflow, ApplicationConfig

config = ApplicationConfig(
    apply_url="https://jobs.example.com/apply/123",
    field_mapping={
        "name": "#full_name",
        "email": "#email",
        "phone": "#phone",
        "cover_letter": "#cover_letter",
    },
    submit_selector="button.submit-application",
    resume_path="/path/to/resume.pdf",
)

workflow = AutoApplyWorkflow(page, config)
result = await workflow.run({
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "cover_letter": "I am excited to apply...",
})

print(f"Success: {result.success}")
print(f"Steps: {len(result.steps)}")
print(f"Failed: {result.failed_steps}")
```

## Adding a New ATS Platform

1. Create an `ApplicationConfig` with the platform's selectors
2. Instantiate `AutoApplyWorkflow` with the config
3. Call `workflow.run()` with candidate data
4. The workflow handles navigation, form filling, upload, and submission

No per-platform code changes needed — just configuration.

## Design Principles

- **Composable**: Steps are independent functions that can be combined
- **Recoverable**: All actions have built-in error handling
- **Observable**: Every step logs duration, status, and errors
- **Testable**: Mock the page for unit tests; use Playwright for integration
- **Configurable**: Field mappings and selectors are external, not hardcoded
