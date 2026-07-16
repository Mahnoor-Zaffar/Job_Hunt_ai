"""Browser Automation Platform.

Components:
- AutomationBrowser: enhanced browser with context/page pools, auth, cookies
- WorkflowEngine: composable step pipeline
- Action Executor: reusable Playwright interactions
- Recovery Engine: exponential backoff retry
- AutoApplyWorkflow: automated ATS job applications
"""

from backend.automation.browser.manager import (
    AuthManager,
    AutomationBrowser,
    ContextPool,
    CookieManager,
    PagePool,
)
from backend.automation.recovery.engine import RecoveryConfig, with_recovery
from backend.automation.workflow.actions import (
    click,
    extract_form_fields,
    extract_text,
    fill_field,
    human_delay,
    navigate,
    scroll_into_view,
    select_option,
    type_text,
    upload_file,
    wait_for_navigation,
    wait_for_selector,
)
from backend.automation.workflow.apply import ApplicationConfig, AutoApplyWorkflow
from backend.automation.workflow.engine import (
    StepResult,
    StepStatus,
    WorkflowEngine,
    WorkflowResult,
    step_click,
    step_extract,
    step_fill,
    step_navigate,
    step_screenshot,
    step_upload,
    step_wait,
)

__all__ = [
    "ApplicationConfig",
    "AuthManager",
    "AutoApplyWorkflow",
    "AutomationBrowser",
    "ContextPool",
    "CookieManager",
    "PagePool",
    "RecoveryConfig",
    "StepResult",
    "StepStatus",
    "WorkflowEngine",
    "WorkflowResult",
    "click",
    "extract_form_fields",
    "extract_text",
    "fill_field",
    "human_delay",
    "navigate",
    "scroll_into_view",
    "select_option",
    "step_click",
    "step_extract",
    "step_fill",
    "step_navigate",
    "step_screenshot",
    "step_upload",
    "step_wait",
    "type_text",
    "upload_file",
    "wait_for_navigation",
    "wait_for_selector",
    "with_recovery",
]
