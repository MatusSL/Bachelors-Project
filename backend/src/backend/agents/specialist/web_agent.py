from backend.schemas.constants import AppType, Priority, PriorityMap
from backend.agents.specialist.base_agent import BaseSpecialistAgent


web_hints_map = {
    # CONTEXT
    "context.app_name": "name of the web application",
    "context.description": "a brief description of what the web application does and its main purpose",
    "context.target_audience": "who the main users are",
    "context.is_public": "whether the application is public or internal",
    # UI
    "ui.is_responsive": "whether the UI must support mobile and desktop screens",
    "ui.has_browser_constraints": "whether the app must support a specific list of browsers, rather than any modern browser",
    "ui.supported_browsers": "which browsers must be supported",
    "ui.has_device_constraints": "whether the app targets a specific list of devices, rather than any device with a modern browser",
    "ui.supported_devices": "which devices are supported",
    "ui.has_dark_mode": "whether the application supports dark mode",
    "ui.has_accessibility_requirements": "whether the application has accessibility requirements",
    "ui.has_animations": "whether the application uses animations",
    # AUTH
    "auth.has_auth": "whether users must log in",
    "auth.auth_types": "authentication methods supported",
    "auth.has_roles": "whether multiple roles exist",
    "auth.roles": "what roles exist",
    "auth.has_admin_panel": "whether there is an admin panel",
    "auth.session_management.has_session_management": "whether the app has session management features",
    "auth.session_management.has_session_expiry": "whether user sessions expire",
    "auth.session_management.has_remember_me": "whether a remember-me option exists",
    "auth.session_management.has_concurrent_session_limit": "whether concurrent session limits are enforced",
    # DATA
    "data.has_forms": "whether the app contains forms",
    "data.has_database": "whether the application uses a database",
    "data.has_file_upload": "whether users can upload files",
    "data.has_file_download": "whether users can download files",
    "data.has_user_generated_content": "whether users can create and share content",
    "data.has_search": "whether the application has search",
    "data.has_pagination": "whether lists require pagination",
    # INTEGRATIONS
    "integrations.has_api": "whether the web app communicates with an API",
    "integrations.api_type": "the API type used, for example REST, GraphQL, or gRPC",
    "integrations.has_payments": "whether payment processing exists",
    "integrations.has_email_notifications": "whether email notifications exist",
    "integrations.has_third_party_services": "whether third-party services are integrated",
    "integrations.third_party_services": "which third-party services are used",
    # NON-FUNCTIONAL
    "non_functional.has_performance_requirements": "whether specific performance targets exist",
    "non_functional.expected_concurrent_users": "the estimated number of users expected to use the app at the same time, for example 100 or 10000",
    "non_functional.has_seo_requirements": "whether SEO optimization is required",
    "non_functional.has_analytics": "whether analytics tracking exists",
    "non_functional.has_error_monitoring": "whether error monitoring is in place",
    # ENVIRONMENT
    "environment.has_multiple_environments": "whether dev/staging/prod environments exist",
    "environment.has_feature_flags": "whether feature flags are used",
    "environment.has_localization": "whether the application supports multiple languages",
    "environment.supported_languages": "which languages are supported",
}


class WebAgent(BaseSpecialistAgent):
    app_type = AppType.WEB
    schema_file = "web.json"
    hints_map = web_hints_map

    def get_domain_rules(self):
        return (
            "Focus on web application requirements including authentication, "
            "UI responsiveness, browser support, databases, integrations, "
            "and deployment environments."
        )

    def get_priority_map(self) -> PriorityMap:
        return {
            Priority.LOW: ["type", "ui", "context", "non-functional"],
            Priority.MEDIUM: ["integrations", "environment"],
            Priority.HIGH: ["auth", "data"],
        }

    def get_risk_rules(self):
        return [
            # AUTH
            {
                "conditions": ["auth.has_auth"],
                "risk": "broken_authentication",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Application includes authentication mechanisms",
            },
            {
                "conditions": ["auth.has_auth", "auth.has_roles"],
                "risk": "authorization_bypass",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Role-based access control may be improperly enforced",
            },
            {
                "conditions": ["auth.has_admin_panel"],
                "risk": "admin_privilege_escalation",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Admin panels are sensitive and require strict access control",
            },
            {
                "conditions": ["auth.session_management.has_session_expiry"],
                "risk": "session_management_issues",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Session expiration logic can be incorrectly implemented",
            },
            {
                "conditions": ["auth.session_management.has_remember_me"],
                "risk": "persistent_session_risk",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "Persistent login increases risk of session hijacking",
            },
            # FORMS
            {
                "conditions": ["data.has_forms"],
                "risk": "invalid_input_handling",
                "category": "validation",
                "priority": Priority.HIGH,
                "reason": "User input through forms must be validated",
            },
            {
                "conditions": ["data.has_forms", "data.has_database"],
                "risk": "sql_injection",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Forms combined with database access enable injection attacks",
            },
            {
                "conditions": ["data.has_forms"],
                "risk": "xss",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "User input rendered in UI may lead to cross-site scripting",
            },
            # DATA
            {
                "conditions": ["data.has_database"],
                "risk": "data_integrity_issues",
                "category": "data",
                "priority": Priority.HIGH,
                "reason": "Persistent data storage must maintain consistency",
            },
            {
                "conditions": ["data.has_user_generated_content"],
                "risk": "stored_xss",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "User-generated content may be rendered to other users",
            },
            # FILES
            {
                "conditions": ["data.has_file_upload"],
                "risk": "malicious_file_upload",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "File uploads may allow malicious content",
            },
            {
                "conditions": ["data.has_file_download"],
                "risk": "insecure_file_access",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "File downloads may expose sensitive data",
            },
            # INTEGRATIONS.API
            {
                "conditions": ["integrations.has_api"],
                "risk": "api_authentication_bypass",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "API endpoints must enforce authentication and authorization",
            },
            {
                "conditions": ["integrations.has_api"],
                "risk": "api_input_validation",
                "category": "validation",
                "priority": Priority.HIGH,
                "reason": "API endpoints accept external input",
            },
            {
                "conditions": ["integrations.has_third_party_services"],
                "risk": "third_party_failure",
                "category": "integration",
                "priority": Priority.MEDIUM,
                "reason": "External services may fail or behave unpredictably",
            },
            {
                "conditions": ["integrations.has_payments"],
                "risk": "payment_integrity",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Payment systems require strict correctness and security",
            },
            # SEARCH / PAGINATION
            {
                "conditions": ["data.has_search"],
                "risk": "search_query_injection",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "Search inputs may be vulnerable to injection or misuse",
            },
            {
                "conditions": ["data.has_pagination"],
                "risk": "pagination_logic_errors",
                "category": "functional",
                "priority": Priority.LOW,
                "reason": "Pagination may skip or duplicate data",
            },
            # UI
            {
                "conditions": ["ui.is_responsive"],
                "risk": "layout_breakage",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Responsive layouts may fail on certain devices",
            },
            {
                "conditions": ["ui.has_accessibility_requirements"],
                "risk": "accessibility_non_compliance",
                "category": "ui",
                "priority": Priority.MEDIUM,
                "reason": "Accessibility requirements must be validated",
            },
            {
                "conditions": ["ui.has_animations"],
                "risk": "ui_performance_issues",
                "category": "performance",
                "priority": Priority.LOW,
                "reason": "Animations can impact performance and usability",
            },
            # NON_FUNCTIONAL
            {
                "conditions": ["non_functional.has_performance_requirements"],
                "risk": "performance_bottlenecks",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "System must meet performance expectations",
            },
            {
                "conditions": ["non_functional.expected_concurrent_users"],
                "risk": "scalability_limits",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "Concurrent usage may overload the system",
            },
            {
                "conditions": ["non_functional.has_error_monitoring"],
                "risk": "undetected_failures",
                "category": "observability",
                "priority": Priority.MEDIUM,
                "reason": "Lack of monitoring may hide system issues",
            },
            # ENVIRONMENT
            {
                "conditions": ["environment.has_multiple_environments"],
                "risk": "environment_config_mismatch",
                "category": "deployment",
                "priority": Priority.MEDIUM,
                "reason": "Differences between environments may cause bugs",
            },
            {
                "conditions": ["environment.has_feature_flags"],
                "risk": "feature_flag_inconsistency",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Feature flags can create inconsistent behavior",
            },
            {
                "conditions": ["environment.has_localization"],
                "risk": "localization_errors",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Multiple languages may introduce UI inconsistencies",
            },
            # EMAIL
            {
                "conditions": ["integrations.has_email_notifications"],
                "risk": "email_delivery_failure",
                "category": "integration",
                "priority": Priority.MEDIUM,
                "reason": "Email notifications may fail to deliver, contain wrong content, or be flagged as spam",
            },
            # SEO
            {
                "conditions": ["non_functional.has_seo_requirements"],
                "risk": "seo_non_compliance",
                "category": "functional",
                "priority": Priority.LOW,
                "reason": "SEO requirements (meta tags, sitemap, structured data) must be validated",
            },
            # ANALYTICS
            {
                "conditions": ["non_functional.has_analytics"],
                "risk": "analytics_tracking_gaps",
                "category": "observability",
                "priority": Priority.LOW,
                "reason": "Analytics events may not fire correctly or may track incorrect data",
            },
        ]
