from backend.schemas.constants import AppType, Priority
from backend.agents.specialist.base_agent import BaseSpecialistAgent


mobile_hints_map = {
    # CONTEXT
    "context.app_name": "name of the mobile application",
    "context.description": "what the application does",
    "context.target_audience": "who the users are",
    "context.platform": "which platforms are supported (ios/android)",
    "context.app_type": "whether the app is native or cross platform",
    "context.minimum_os_versions.has_ios": "whether the app supports iOS",
    "context.minimum_os_versions.ios": "minimum iOS version supported",
    "context.minimum_os_versions.has_android": "whether the app supports Android",
    "context.minimum_os_versions.android": "minimum Android version supported",

    # DISTRIBUTION
    "distribution.has_distribution_channels": "whether the app has specific distribution channels",
    "distribution.distribution_channels": "where the app will be distributed",
    "distribution.has_in_app_purchases": "whether the app contains in-app purchases",
    "distribution.has_ads": "whether the app shows ads",

    # UI
    "ui.has_target_screen_sizes": "whether the app targets specific screen sizes or device types, rather than any phone or tablet",
    "ui.target_screen_sizes": "target screen sizes or device types",
    "ui.has_landscape_support": "whether landscape orientation is supported",
    "ui.has_dark_mode": "whether the app supports dark mode",
    "ui.has_accessibility_requirements": "whether the app has accessibility requirements",
    "ui.has_animations": "whether the app uses animations",
    "ui.has_gestures": "whether the app uses gesture-based interactions",

    # AUTH
    "auth.has_auth": "whether users must log in",
    "auth.auth_types": "authentication methods",
    "auth.has_biometric_auth": "whether biometric login is supported",
    "auth.has_roles": "whether multiple user roles exist",
    "auth.roles": "what user roles exist",
    "auth.session_management.has_session_expiry": "whether user sessions expire",
    "auth.session_management.has_auto_lock": "whether the app auto-locks after inactivity",

    # DEVICE FEATURES
    "device_features.has_camera": "whether the app uses the camera",
    "device_features.has_microphone": "whether the app uses the microphone",
    "device_features.has_location": "whether the app uses location",
    "device_features.has_push_notifications": "whether push notifications exist",
    "device_features.has_contacts_access": "whether the app accesses contacts",
    "device_features.has_storage_access": "whether the app accesses device storage",
    "device_features.has_bluetooth": "whether the app uses Bluetooth",
    "device_features.has_nfc": "whether the app uses NFC",
    "device_features.has_biometrics": "whether the app uses biometric features",

    # DATA
    "data.has_forms": "whether the app contains forms",
    "data.has_offline_mode": "whether the app works offline",
    "data.has_local_storage": "whether the app stores data locally",
    "data.has_file_upload": "whether users can upload files",
    "data.has_database": "whether the app uses a database",
    "data.has_search": "whether the app has search functionality",

    # INTEGRATIONS
    "integrations.has_api": "whether the app communicates with an API",
    "integrations.has_payments": "whether payments exist",
    "integrations.has_deep_links": "whether deep linking is supported",
    "integrations.has_third_party_sdks": "whether third-party SDKs are integrated",
    "integrations.third_party_sdks": "which third-party SDKs are used",
    "integrations.has_social_sharing": "whether social sharing is supported",

    # NON-FUNCTIONAL
    "non_functional.has_performance_requirements": "whether specific performance targets exist",
    "non_functional.has_low_end_device_testing": "whether testing on low-end devices is needed",
    "non_functional.has_crash_reporting": "whether crash reporting is in place",
    "non_functional.app_update_behavior.has_force_update": "whether forced app updates exist",
    "non_functional.app_update_behavior.has_migration": "whether data migration is needed on updates",

    # ENVIRONMENT
    "environment.has_multiple_environments": "whether dev/staging/prod environments exist",
    "environment.has_feature_flags": "whether feature flags are used",
    "environment.has_localization": "whether the app supports multiple languages",
    "environment.supported_languages": "which languages are supported",
}


class MobileAgent(BaseSpecialistAgent):
    app_type = AppType.MOBILE
    schema_file = "mobile.json"
    hints_map = mobile_hints_map

    def get_domain_rules(self):
        return (
            "Focus on mobile constraints including platforms, device permissions, "
            "offline support, push notifications, app store distribution, and UI behavior."
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
                "conditions": ["auth.has_biometric_auth"],
                "risk": "biometric_auth_failure",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Biometric authentication requires secure handling",
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
            # DEVICE FEATURES
            {
                "conditions": ["device_features.has_camera"],
                "risk": "camera_permission_abuse",
                "category": "privacy",
                "priority": Priority.HIGH,
                "reason": "Camera access must be properly secured and disclosed",
            },
            {
                "conditions": ["device_features.has_location"],
                "risk": "location_privacy_leak",
                "category": "privacy",
                "priority": Priority.HIGH,
                "reason": "Location data is sensitive and must be protected",
            },
            {
                "conditions": ["device_features.has_microphone"],
                "risk": "microphone_abuse",
                "category": "privacy",
                "priority": Priority.HIGH,
                "reason": "Microphone access may expose sensitive information",
            },
            {
                "conditions": ["device_features.has_push_notifications"],
                "risk": "notification_spam_or_abuse",
                "category": "functional",
                "priority": Priority.LOW,
                "reason": "Push notifications may degrade user experience",
            },
            {
                "conditions": ["device_features.has_storage_access"],
                "risk": "insecure_local_storage",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Sensitive data stored locally may be exposed",
            },
            {
                "conditions": ["device_features.has_biometrics"],
                "risk": "biometric_data_misuse",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Biometric data must be handled securely",
            },
            # DATA
            {
                "conditions": ["data.has_forms"],
                "risk": "invalid_input_handling",
                "category": "validation",
                "priority": Priority.HIGH,
                "reason": "User input through forms must be validated",
            },
            {
                "conditions": ["data.has_forms", "data.has_database"],
                "risk": "injection_attacks",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Forms combined with database access enable injection attacks",
            },
            {
                "conditions": ["data.has_offline_mode"],
                "risk": "data_sync_conflicts",
                "category": "data",
                "priority": Priority.MEDIUM,
                "reason": "Offline mode can cause synchronization inconsistencies",
            },
            {
                "conditions": ["data.has_local_storage"],
                "risk": "data_persistence_issues",
                "category": "data",
                "priority": Priority.MEDIUM,
                "reason": "Locally stored data may become inconsistent or corrupted",
            },
            {
                "conditions": ["data.has_file_upload"],
                "risk": "malicious_file_upload",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "File uploads may allow malicious content",
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
                "conditions": ["integrations.has_payments"],
                "risk": "payment_integrity",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Payment systems require strict correctness and security",
            },
            {
                "conditions": ["integrations.has_third_party_sdks"],
                "risk": "third_party_sdk_risk",
                "category": "integration",
                "priority": Priority.MEDIUM,
                "reason": "Third-party SDKs may introduce vulnerabilities or instability",
            },
            {
                "conditions": ["integrations.has_deep_links"],
                "risk": "deep_link_hijacking",
                "category": "security",
                "priority": Priority.HIGH,
                "reason": "Deep links may be exploited if not validated properly",
            },
            # UI
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
            {
                "conditions": ["ui.has_gestures"],
                "risk": "gesture_handling_errors",
                "category": "ui",
                "priority": Priority.LOW,
                "reason": "Gesture-based interactions may be inconsistent",
            },
            # NON-FUNCTIONAL
            {
                "conditions": ["non_functional.has_performance_requirements"],
                "risk": "performance_bottlenecks",
                "category": "performance",
                "priority": Priority.HIGH,
                "reason": "App must meet performance expectations on mobile devices",
            },
            {
                "conditions": ["non_functional.has_low_end_device_testing"],
                "risk": "low_end_device_failures",
                "category": "performance",
                "priority": Priority.MEDIUM,
                "reason": "App may not perform well on low-end devices",
            },
            {
                "conditions": ["non_functional.has_crash_reporting"],
                "risk": "undetected_crashes",
                "category": "observability",
                "priority": Priority.MEDIUM,
                "reason": "Lack of crash reporting may hide critical issues",
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
        ]
