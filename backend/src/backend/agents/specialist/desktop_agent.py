from backend.schemas.constants import AppType, Priority
from backend.agents.specialist.base_agent import BaseSpecialistAgent


desktop_hints_map = {
    # CONTEXT
    "context.app_name": "name of the desktop application",
    "context.description": "what the application does",
    "context.target_audience": "who uses the application",
    "context.app_framework": "which framework is used (Electron, Qt, .NET etc)",
    "context.supported_os": "which operating systems are supported",
    "context.supported_architectures": "which CPU architectures are supported",

    # INSTALLATION
    "installation.has_installer": "whether the app has an installer",
    "installation.has_silent_install": "whether silent/unattended installation is supported",
    "installation.has_admin_rights": "whether installation requires admin rights",
    "installation.has_auto_updater": "whether the app auto updates",
    "installation.has_uninstaller": "whether a dedicated uninstaller exists",
    "installation.has_license_activation": "whether license activation is required",

    # UI
    "ui.has_multiple_windows": "whether multiple windows exist",
    "ui.has_system_tray": "whether the app uses system tray",
    "ui.has_keyboard_shortcuts": "whether keyboard shortcuts exist",
    "ui.has_drag_and_drop": "whether drag and drop is supported",
    "ui.has_high_dpi_support": "whether the app supports high DPI displays",
    "ui.has_accessibility_requirements": "whether the app has accessibility requirements",
    "ui.has_context_menus": "whether context menus exist",
    "ui.has_dark_mode": "whether the app supports dark mode",

    # AUTH
    "auth.has_auth": "whether login is required",
    "auth.auth_types": "authentication methods",
    "auth.has_roles": "whether multiple user roles exist",
    "auth.roles": "what user roles exist",
    "auth.session_management.has_session_expiry": "whether user sessions expire",
    "auth.session_management.has_auto_lock": "whether the app auto-locks after inactivity",

    # DATA
    "data.has_file_operations": "whether the app manipulates files",
    "data.supported_file_formats": "which file formats are supported",
    "data.has_import_export": "whether import and export functionality exists",
    "data.has_local_database": "whether the app stores data locally",
    "data.has_cloud_sync": "whether data syncs to the cloud",
    "data.has_large_file_handling": "whether the app handles large files",
    "data.has_undo_redo": "whether undo and redo are supported",

    # OS INTEGRATION
    "os_integration.has_file_system_permissions": "whether the app requires specific file system permissions",
    "os_integration.has_registry_access": "whether the app reads or writes the OS registry",
    "os_integration.has_notifications": "whether OS notifications are used",
    "os_integration.has_clipboard": "whether clipboard is used",
    "os_integration.has_printing": "whether printing functionality exists",
    "os_integration.has_shell_integration": "whether shell or file explorer integration exists",
    "os_integration.has_startup_launch": "whether the app launches on system startup",

    # INTEGRATIONS
    "integrations.has_api": "whether the app calls external APIs",
    "integrations.has_third_party_integrations": "whether third-party integrations exist",
    "integrations.third_party_integrations": "which third-party integrations are used",
    "integrations.has_plugin_system": "whether plugin system exists",

    # NON-FUNCTIONAL
    "non_functional.has_performance_requirements": "whether specific performance targets exist",
    "non_functional.has_minimum_spec_testing": "whether testing on minimum spec hardware is needed",
    "non_functional.has_crash_reporting": "whether crash reporting is in place",
    "non_functional.has_long_running_session_testing": "whether long-running session stability must be tested",

    # ENVIRONMENT
    "environment.has_multiple_environments": "whether dev/staging/prod environments exist",
    "environment.has_feature_flags": "whether feature flags are used",
    "environment.has_localization": "whether the app supports multiple languages",
    "environment.supported_languages": "which languages are supported",
    "environment.is_enterprise_deployed": "whether the app is deployed in enterprise environments",
}


class DesktopAgent(BaseSpecialistAgent):
    app_type = AppType.DESKTOP
    schema_file = "desktop.json"
    hints_map = desktop_hints_map

    def get_domain_rules(self):
        return (
            "Focus on desktop application requirements including installation, "
            "OS integration, file handling, performance constraints, and UI features."
        )

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
                "conditions": ["auth.session_management.has_session_expiry"],
                "risk": "session_management_issues",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Session expiration logic can be incorrectly implemented",
            },
            {
                "conditions": ["auth.session_management.has_auto_lock"],
                "risk": "insecure_session_lock",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "Auto-lock mechanisms may be bypassed or misconfigured",
            },
            # INSTALLATION
            {
                "conditions": ["installation.has_installer"],
                "risk": "installer_failures",
                "category": "deployment",
                "priority": Priority.HIGH,
                "reason": "Installer may fail or misconfigure the application",
            },
            {
                "conditions": ["installation.has_admin_rights"],
                "risk": "privilege_escalation_risk",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Admin rights increase risk of misuse or escalation",
            },
            {
                "conditions": ["installation.has_auto_updater"],
                "risk": "insecure_auto_update",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Auto-update mechanisms can be exploited if not secured",
            },
            {
                "conditions": ["installation.has_uninstaller"],
                "risk": "incomplete_uninstall",
                "category": "deployment",
                "priority": Priority.MEDIUM,
                "reason": "Uninstaller may leave residual files or configs",
            },
            {
                "conditions": ["installation.has_license_activation"],
                "risk": "license_bypass",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "License enforcement mechanisms may be bypassed",
            },
            # UI
            {
                "conditions": ["ui.has_multiple_windows"],
                "risk": "window_state_inconsistency",
                "category": "ui",
                "priority": Priority.MEDIUM,
                "reason": "Multiple windows may lead to inconsistent state handling",
            },
            {
                "conditions": ["ui.has_system_tray"],
                "risk": "background_execution_confusion",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "System tray apps may confuse users about running state",
            },
            {
                "conditions": ["ui.has_keyboard_shortcuts"],
                "risk": "shortcut_conflicts",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Keyboard shortcuts may conflict with OS or user expectations",
            },
            {
                "conditions": ["ui.has_drag_and_drop"],
                "risk": "invalid_input_via_drag_drop",
                "category": "validation",
                "priority": Priority.MEDIUM,
                "reason": "Drag and drop may introduce unvalidated input",
            },
            {
                "conditions": ["ui.has_high_dpi_support"],
                "risk": "dpi_scaling_issues",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "High DPI support may cause rendering issues",
            },
            {
                "conditions": ["ui.has_accessibility_requirements"],
                "risk": "accessibility_non_compliance",
                "category": "ui",
                "priority": Priority.MEDIUM,
                "reason": "Accessibility requirements must be validated",
            },
            {
                "conditions": ["ui.has_dark_mode"],
                "risk": "theme_inconsistency",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Dark mode may introduce visual inconsistencies",
            },
            # DATA
            {
                "conditions": ["data.has_file_operations"],
                "risk": "file_corruption_or_loss",
                "category": "data",
                "priority": Priority.HIGH,
                "reason": "File operations may corrupt or lose user data",
            },
            {
                "conditions": ["data.has_file_operations"],
                "risk": "path_traversal",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "File handling may allow unauthorized file access",
            },
            {
                "conditions": ["data.has_import_export"],
                "risk": "malicious_file_import",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Imported files may contain malicious content",
            },
            {
                "conditions": ["data.has_local_database"],
                "risk": "insecure_local_storage",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Locally stored data may be exposed",
            },
            {
                "conditions": ["data.has_cloud_sync"],
                "risk": "sync_conflicts",
                "category": "data",
                "priority": Priority.MEDIUM,
                "reason": "Cloud sync may introduce inconsistencies",
            },
            {
                "conditions": ["data.has_large_file_handling"],
                "risk": "memory_or_performance_issues",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "Large files may impact performance or stability",
            },
            {
                "conditions": ["data.has_undo_redo"],
                "risk": "state_management_errors",
                "category": "functional",
                "priority": Priority.MEDIUM,
                "reason": "Undo/redo systems require consistent state handling",
            },
            # OS INTEGRATION
            {
                "conditions": ["os_integration.has_file_system_permissions"],
                "risk": "permission_misconfiguration",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Incorrect permissions may expose sensitive data",
            },
            {
                "conditions": ["os_integration.has_registry_access"],
                "risk": "registry_corruption",
                "category": "system",
                "priority": Priority.MEDIUM,
                "reason": "Registry modifications may destabilize the system",
            },
            {
                "conditions": ["os_integration.has_notifications"],
                "risk": "notification_spam",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Excessive notifications may degrade UX",
            },
            {
                "conditions": ["os_integration.has_clipboard"],
                "risk": "clipboard_data_leak",
                "category": "privacy",
                "priority": Priority.MEDIUM,
                "reason": "Clipboard usage may expose sensitive data",
            },
            {
                "conditions": ["os_integration.has_printing"],
                "risk": "printing_failures",
                "category": "functional",
                "priority": Priority.LOW,
                "reason": "Printing workflows may fail across environments",
            },
            {
                "conditions": ["os_integration.has_shell_integration"],
                "risk": "shell_injection",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Shell integration may allow command injection",
            },
            {
                "conditions": ["os_integration.has_startup_launch"],
                "risk": "startup_abuse",
                "category": "security",
                "priority": Priority.MEDIUM,
                "reason": "Startup launch may be abused or annoy users",
            },
            # INTEGRATIONS
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
                "conditions": ["integrations.has_third_party_integrations"],
                "risk": "third_party_dependency_risk",
                "category": "integration",
                "priority": Priority.MEDIUM,
                "reason": "External integrations may introduce vulnerabilities",
            },
            {
                "conditions": ["integrations.has_plugin_system"],
                "risk": "untrusted_plugin_execution",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Plugins may execute untrusted code",
            },
            # NON-FUNCTIONAL
            {
                "conditions": ["non_functional.has_performance_requirements"],
                "risk": "performance_bottlenecks",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "App must meet performance expectations",
            },
            {
                "conditions": ["non_functional.has_minimum_spec_testing"],
                "risk": "low_spec_failures",
                "category": "performance",
                "priority": Priority.MEDIUM,
                "reason": "App may not perform on minimum spec machines",
            },
            {
                "conditions": ["non_functional.has_crash_reporting"],
                "risk": "undetected_crashes",
                "category": "observability",
                "priority": Priority.MEDIUM,
                "reason": "Lack of crash reporting may hide critical issues",
            },
            {
                "conditions": ["non_functional.has_long_running_session_testing"],
                "risk": "memory_leaks_or_state_drift",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "Long-running sessions may expose leaks or instability",
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
            {
                "conditions": ["environment.is_enterprise_deployed"],
                "risk": "enterprise_deployment_issues",
                "category": "deployment",
                "priority": Priority.MEDIUM,
                "reason": "Enterprise environments introduce additional constraints",
            },
        ]
