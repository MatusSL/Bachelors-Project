from backend.schemas.constants import AppType, Priority
from backend.agents.specialist.base_agent import BaseSpecialistAgent


api_hints_map = {
    # CONTEXT
    "context.api_name": "name of the API",
    "context.description": "what the API does",
    "context.api_type": "type of API (REST, GraphQL, gRPC)",
    "context.base_url": "base URL of the API",
    "context.version": "API version",
    "context.has_consumers": "whether there is a known list of consumers, rather than a public or undefined audience",
    "context.consumers": "who or what consumes this API",
    "context.has_documentation": "whether public or internal API documentation exists at a URL",
    "context.documentation_url": "where API documentation is hosted",

    # AUTH
    "auth.has_auth": "whether the API requires authentication",
    "auth.auth_types": "authentication methods supported",
    "auth.has_roles": "whether role-based access control exists",
    "auth.roles": "what roles exist",
    "auth.has_scopes": "whether OAuth scopes are used",
    "auth.token_behavior.has_expiry": "whether tokens expire",
    "auth.token_behavior.has_refresh_token": "whether refresh tokens are supported",
    "auth.token_behavior.has_token_revocation": "whether token revocation is supported",

    # ENDPOINTS
    "endpoints.has_crud_operations": "whether the API provides CRUD operations",
    "endpoints.has_bulk_operations": "whether bulk operations exist",
    "endpoints.has_file_upload": "whether file upload endpoints exist",
    "endpoints.has_file_download": "whether file download endpoints exist",
    "endpoints.has_search_filter": "whether search or filter endpoints exist",
    "endpoints.has_pagination": "whether paginated responses exist",
    "endpoints.has_sorting": "whether sortable responses exist",
    "endpoints.has_webhooks": "whether the API sends webhooks",
    "endpoints.has_websockets": "whether the API uses WebSockets",

    # DATA
    "data.has_database": "whether the API uses a database",
    "data.has_input_validation": "whether input validation exists",
    "data.has_data_transformation": "whether data transformation occurs",
    "data.has_sensitive_data": "whether the API handles any sensitive data fields (PII, secrets, payment info, etc.)",
    "data.sensitive_data_fields": "which fields contain sensitive data",

    # RESPONSE BEHAVIOR
    "response_behavior.has_http_standards": "whether HTTP status codes follow standards",
    "response_behavior.has_consistent_error_format": "whether error responses follow a consistent format",
    "response_behavior.has_versioning": "whether API versioning exists",
    "response_behavior.has_sensitive_data_in_errors": "whether error responses may leak sensitive data",

    # NON-FUNCTIONAL
    "non_functional.has_rate_limiting": "whether rate limiting exists",
    "non_functional.has_performance_requirements": "whether specific performance targets exist",
    "non_functional.expected_requests_per_second": "expected request load, for example 100 or 10000",
    "non_functional.has_caching": "whether caching is implemented",
    "non_functional.has_idempotency": "whether endpoints are idempotent",
    "non_functional.has_circuit_breaker": "whether circuit breakers are implemented",

    # INTEGRATIONS
    "integrations.has_external_api_calls": "whether the API calls external APIs",
    "integrations.external_apis": "which external APIs are called",
    "integrations.has_message_queue": "whether message queues are used",
    "integrations.has_database_migrations": "whether database migrations are managed",

    # SECURITY
    "security.has_injection_testing": "whether injection attack testing is required",
    "security.has_mass_assignment_testing": "whether mass assignment vulnerabilities must be tested",
    "security.has_bola_testing": "whether BOLA testing is required",
    "security.has_cors_config": "whether CORS is configured",

    # ENVIRONMENT
    "environment.has_multiple_environments": "whether dev/staging/prod environments exist",
    "environment.has_feature_flags": "whether feature flags are used",
    "environment.has_api_mocks_for_consumers": "whether API mocks exist for consumers",
}


class APIAgent(BaseSpecialistAgent):
    app_type = AppType.API
    schema_file = "api.json"
    hints_map = api_hints_map

    def get_domain_rules(self):
        return (
            "Focus on API architecture including endpoints, authentication, "
            "rate limiting, pagination, caching, and integrations."
        )

    def get_risk_rules(self):
        return [
            # AUTH
            {
                "conditions": ["auth.has_auth"],
                "risk": "broken_authentication",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "API includes authentication mechanisms",
            },
            {
                "conditions": ["auth.has_auth", "auth.has_roles"],
                "risk": "authorization_bypass",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Role-based access control may be improperly enforced",
            },
            {
                "conditions": ["auth.has_scopes"],
                "risk": "scope_misconfiguration",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "OAuth scopes may be incorrectly enforced",
            },
            {
                "conditions": ["auth.token_behavior.has_expiry"],
                "risk": "token_expiry_handling",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "Improper token expiry handling may allow unauthorized access",
            },
            {
                "conditions": ["auth.token_behavior.has_refresh_token"],
                "risk": "refresh_token_abuse",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Refresh tokens can be abused if not secured properly",
            },
            {
                "conditions": ["auth.token_behavior.has_token_revocation"],
                "risk": "token_revocation_failure",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Token revocation mechanisms may not work correctly",
            },
            # ENDPOINTS
            {
                "conditions": ["endpoints.has_crud_operations"],
                "risk": "broken_object_level_authorization",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "CRUD APIs are vulnerable to BOLA if not properly secured",
            },
            {
                "conditions": ["endpoints.has_bulk_operations"],
                "risk": "bulk_operation_abuse",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Bulk operations may amplify impact of misuse",
            },
            {
                "conditions": ["endpoints.has_file_upload"],
                "risk": "malicious_file_upload",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "File upload endpoints may allow malicious content",
            },
            {
                "conditions": ["endpoints.has_file_download"],
                "risk": "insecure_file_access",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "File downloads may expose unauthorized data",
            },
            {
                "conditions": ["endpoints.has_search_filter"],
                "risk": "query_injection",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Search and filter parameters may be injectable",
            },
            {
                "conditions": ["endpoints.has_pagination"],
                "risk": "pagination_inconsistency",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Pagination logic may be inconsistent or incorrect",
            },
            {
                "conditions": ["endpoints.has_webhooks"],
                "risk": "webhook_spoofing",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Webhooks may be spoofed without proper verification",
            },
            {
                "conditions": ["endpoints.has_websockets"],
                "risk": "websocket_auth_bypass",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "WebSocket connections may bypass authentication",
            },
            # DATA
            {
                "conditions": ["data.has_database"],
                "risk": "injection_attacks",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Database usage introduces injection risks",
            },
            {
                "conditions": ["data.has_input_validation"],
                "risk": "insufficient_input_validation",
                "category": "validation",
                "priority": Priority.HIGH,
                "reason": "Input validation may be incomplete or bypassable",
            },
            {
                "conditions": ["data.has_data_transformation"],
                "risk": "data_transformation_errors",
                "category": "data",
                "priority": Priority.MEDIUM,
                "reason": "Transformations may introduce inconsistencies",
            },
            {
                "conditions": ["data.sensitive_data_fields"],
                "risk": "sensitive_data_exposure",
                "category": "privacy",
                "priority": Priority.HIGH,
                "reason": "Sensitive fields must be protected in storage and transit",
            },
            # RESPONSE BEHAVIOR
            {
                "conditions": ["response_behavior.has_consistent_error_format"],
                "risk": "error_handling_inconsistency",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Inconsistent errors complicate client handling",
            },
            {
                "conditions": ["response_behavior.has_sensitive_data_in_errors"],
                "risk": "information_leakage",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Error responses may leak sensitive data",
            },
            {
                "conditions": ["response_behavior.has_versioning"],
                "risk": "versioning_breaking_changes",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Improper versioning may break clients",
            },
            # NON-FUNCTIONAL
            {
                "conditions": ["non_functional.has_rate_limiting"],
                "risk": "rate_limit_bypass",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Rate limiting may be bypassed or misconfigured",
            },
            {
                "conditions": ["non_functional.has_caching"],
                "risk": "cache_inconsistency_or_leak",
                "category": "performance",
                "priority": Priority.MEDIUM,
                "reason": "Caching may return stale or unauthorized data",
            },
            {
                "conditions": ["non_functional.has_idempotency"],
                "risk": "idempotency_violation",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Non-idempotent operations may cause duplicate effects",
            },
            {
                "conditions": ["non_functional.has_circuit_breaker"],
                "risk": "circuit_breaker_misconfiguration",
                "category": "resilience",
                "priority": Priority.MEDIUM,
                "reason": "Circuit breakers may not trigger correctly",
            },
            {
                "conditions": ["non_functional.has_performance_requirements"],
                "risk": "performance_bottlenecks",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "API must meet performance expectations",
            },
            # INTEGRATIONS
            {
                "conditions": ["integrations.has_external_api_calls"],
                "risk": "third_party_dependency_failure",
                "category": "integration",
                "priority": Priority.MEDIUM,
                "reason": "External APIs may fail or behave unpredictably",
            },
            {
                "conditions": ["integrations.has_message_queue"],
                "risk": "message_loss_or_duplication",
                "category": "data",
                "priority": Priority.MEDIUM,
                "reason": "Queues may lose or duplicate messages",
            },
            {
                "conditions": ["integrations.has_database_migrations"],
                "risk": "migration_failure",
                "category": "deployment",
                "priority": Priority.HIGH,
                "reason": "Database migrations may corrupt or lose data",
            },
            # SECURITY FLAGS
            {
                "conditions": ["security.has_mass_assignment_testing"],
                "risk": "mass_assignment",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Mass assignment vulnerabilities may exist",
            },
            {
                "conditions": ["security.has_cors_config"],
                "risk": "cors_misconfiguration",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Improper CORS config may expose API to abuse",
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
                "conditions": ["environment.has_api_mocks_for_consumers"],
                "risk": "mock_vs_real_behavior_drift",
                "category": "testing",
                "priority": Priority.LOW,
                "reason": "Mocks may diverge from real API behavior",
            },
        ]
