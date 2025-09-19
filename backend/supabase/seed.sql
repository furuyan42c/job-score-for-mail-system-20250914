-- T074: Deployment Seed Data
-- Initial data for production deployment

-- Insert additional email templates
INSERT INTO email_templates (template_name, type, notification_type, subject, content, active) VALUES
('welcome_email', 'transactional', 'welcome', 'Welcome to Mail Score!', '{
    "html": "<h1>Welcome to Mail Score!</h1><p>Hello {{name}},</p><p>Thank you for joining Mail Score. We''re excited to help you improve your email performance.</p><p><a href=\"{{dashboard_url}}\">Get Started</a></p>",
    "text": "Welcome to Mail Score!\n\nHello {{name}},\n\nThank you for joining Mail Score. We''re excited to help you improve your email performance.\n\nGet Started: {{dashboard_url}}"
}', true),

('password_reset', 'transactional', 'auth', 'Reset Your Password', '{
    "html": "<h2>Password Reset Request</h2><p>Click the link below to reset your password:</p><p><a href=\"{{reset_url}}\">Reset Password</a></p><p>This link will expire in 1 hour.</p>",
    "text": "Password Reset Request\n\nClick the link below to reset your password:\n{{reset_url}}\n\nThis link will expire in 1 hour."
}', true),

('email_verification', 'transactional', 'auth', 'Verify Your Email Address', '{
    "html": "<h2>Email Verification</h2><p>Please verify your email address by clicking the link below:</p><p><a href=\"{{verification_url}}\">Verify Email</a></p>",
    "text": "Email Verification\n\nPlease verify your email address by clicking the link below:\n{{verification_url}}"
}', true),

('score_alert_high', 'notification', 'score_alert', 'High Score Alert - {{entity_type}} {{entity_id}}', '{
    "html": "<h2>🎉 High Score Alert!</h2><p>Great news! Your {{entity_type}} <strong>{{entity_id}}</strong> has achieved a high score:</p><ul><li><strong>Overall Score:</strong> {{overall_score}}/100</li><li><strong>Confidence:</strong> {{confidence}}%</li><li><strong>Top Category:</strong> {{top_category}} ({{top_score}})</li></ul><p><a href=\"{{details_url}}\">View Details</a></p>",
    "text": "🎉 High Score Alert!\n\nGreat news! Your {{entity_type}} {{entity_id}} has achieved a high score:\n\n- Overall Score: {{overall_score}}/100\n- Confidence: {{confidence}}%\n- Top Category: {{top_category}} ({{top_score}})\n\nView Details: {{details_url}}"
}', true),

('score_alert_low', 'notification', 'score_alert', 'Low Score Alert - {{entity_type}} {{entity_id}}', '{
    "html": "<h2>⚠️ Low Score Alert</h2><p>Your {{entity_type}} <strong>{{entity_id}}</strong> has received a low score:</p><ul><li><strong>Overall Score:</strong> {{overall_score}}/100</li><li><strong>Confidence:</strong> {{confidence}}%</li><li><strong>Improvement Area:</strong> {{improvement_area}}</li></ul><p><a href=\"{{improvement_url}}\">Get Improvement Tips</a></p>",
    "text": "⚠️ Low Score Alert\n\nYour {{entity_type}} {{entity_id}} has received a low score:\n\n- Overall Score: {{overall_score}}/100\n- Confidence: {{confidence}}%\n- Improvement Area: {{improvement_area}}\n\nGet Improvement Tips: {{improvement_url}}"
}', true),

('bulk_operation_complete', 'notification', 'bulk_operation', 'Bulk Operation Complete - {{operation_type}}', '{
    "html": "<h2>Bulk Operation Complete</h2><p>Your {{operation_type}} operation has finished:</p><ul><li><strong>Total Items:</strong> {{total_items}}</li><li><strong>Successful:</strong> {{successful_items}}</li><li><strong>Failed:</strong> {{failed_items}}</li><li><strong>Duration:</strong> {{duration}}</li></ul><p><a href=\"{{results_url}}\">View Full Results</a></p>",
    "text": "Bulk Operation Complete\n\nYour {{operation_type}} operation has finished:\n\n- Total Items: {{total_items}}\n- Successful: {{successful_items}}\n- Failed: {{failed_items}}\n- Duration: {{duration}}\n\nView Full Results: {{results_url}}"
}', true),

('system_maintenance', 'notification', 'system', 'Scheduled Maintenance - {{maintenance_date}}', '{
    "html": "<h2>🔧 Scheduled Maintenance Notice</h2><p>We will be performing scheduled maintenance on {{maintenance_date}} from {{start_time}} to {{end_time}} ({{timezone}}).</p><p><strong>Expected Impact:</strong> {{impact_description}}</p><p>We apologize for any inconvenience and appreciate your patience.</p>",
    "text": "🔧 Scheduled Maintenance Notice\n\nWe will be performing scheduled maintenance on {{maintenance_date}} from {{start_time}} to {{end_time}} ({{timezone}}).\n\nExpected Impact: {{impact_description}}\n\nWe apologize for any inconvenience and appreciate your patience."
}', true)

ON CONFLICT (template_name) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = NOW();

-- Insert additional system configuration
INSERT INTO system_config (key, value, description) VALUES
('notification_settings', '{
    "email_enabled": true,
    "push_enabled": false,
    "sms_enabled": false,
    "default_notification_types": ["job_completion", "score_alerts", "system_status"],
    "frequency_limits": {
        "per_user_per_hour": 10,
        "per_user_per_day": 50
    }
}', 'Global notification settings'),

('score_thresholds', '{
    "high_score_threshold": 85,
    "low_score_threshold": 40,
    "confidence_threshold": 0.7,
    "alert_thresholds": {
        "email_score": {"high": 90, "low": 30},
        "matching_score": {"high": 95, "low": 50},
        "performance_score": {"high": 95, "low": 60}
    }
}', 'Score alert thresholds'),

('performance_targets', '{
    "latency_ms": {"excellent": 100, "good": 500, "poor": 2000},
    "throughput": {"excellent": 1000, "good": 500, "poor": 100},
    "accuracy": {"excellent": 0.98, "good": 0.90, "poor": 0.80},
    "uptime": {"excellent": 0.999, "good": 0.995, "poor": 0.99},
    "efficiency": {"excellent": 0.95, "good": 0.85, "poor": 0.70}
}', 'Performance metric targets'),

('file_retention_policy', '{
    "temp_files_days": 1,
    "csv_imports_days": 30,
    "email_attachments_days": 90,
    "log_files_days": 180,
    "auto_cleanup_enabled": true,
    "cleanup_schedule": "daily"
}', 'File retention and cleanup policy'),

('api_rate_limits', '{
    "authenticated_user": {
        "requests_per_minute": 100,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "anonymous_user": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500
    },
    "bulk_operations": {
        "max_batch_size": 1000,
        "max_concurrent_batches": 5,
        "cooldown_seconds": 30
    }
}', 'API rate limiting configuration'),

('feature_flags', '{
    "realtime_enabled": true,
    "email_notifications": true,
    "bulk_operations": true,
    "performance_monitoring": true,
    "advanced_scoring": true,
    "file_processing": true,
    "csv_import": true,
    "email_attachments": true,
    "beta_features": false
}', 'Feature toggles and flags')

ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Insert sample performance metrics for dashboard
INSERT INTO performance_metrics (entity_id, entity_type, metric_type, latency_ms, throughput, accuracy, uptime, efficiency, metadata, recorded_at) VALUES
(gen_random_uuid(), 'system', 'api_performance', 120, 850.5, 0.98, 0.999, 0.92, '{"endpoint": "/api/scores", "method": "POST"}', NOW() - INTERVAL '1 hour'),
(gen_random_uuid(), 'system', 'api_performance', 95, 920.3, 0.99, 0.999, 0.94, '{"endpoint": "/api/files", "method": "POST"}', NOW() - INTERVAL '2 hours'),
(gen_random_uuid(), 'system', 'api_performance', 180, 720.1, 0.96, 0.998, 0.89, '{"endpoint": "/api/calculations", "method": "POST"}', NOW() - INTERVAL '3 hours'),
(gen_random_uuid(), 'system', 'database_performance', 45, 1200.0, 0.995, 0.9995, 0.96, '{"operation": "select", "table": "score_calculations"}', NOW() - INTERVAL '30 minutes'),
(gen_random_uuid(), 'system', 'database_performance', 65, 950.0, 0.993, 0.9995, 0.94, '{"operation": "insert", "table": "background_jobs"}', NOW() - INTERVAL '45 minutes'),
(gen_random_uuid(), 'system', 'storage_performance', 250, 500.0, 0.99, 0.997, 0.91, '{"operation": "upload", "bucket": "files"}', NOW() - INTERVAL '1.5 hours'),
(gen_random_uuid(), 'system', 'storage_performance', 180, 650.0, 0.995, 0.998, 0.93, '{"operation": "download", "bucket": "csv-imports"}', NOW() - INTERVAL '2.5 hours');

-- Insert sample email configuration for different environments
INSERT INTO email_config (config_name, config, active) VALUES
('sendgrid_production', '{
    "service": "sendgrid",
    "api_key": "SG.REPLACE_WITH_ACTUAL_KEY",
    "default_from": "noreply@mailscore.app",
    "notification_from": "notifications@mailscore.app",
    "bulk_from": "bulk@mailscore.app",
    "reply_to": "support@mailscore.app",
    "tracking": {
        "open_tracking": true,
        "click_tracking": true,
        "subscription_tracking": false
    }
}', false),

('aws_ses_production', '{
    "service": "aws_ses",
    "region": "us-east-1",
    "access_key_id": "REPLACE_WITH_ACTUAL_KEY",
    "secret_access_key": "REPLACE_WITH_ACTUAL_SECRET",
    "default_from": "noreply@mailscore.app",
    "notification_from": "notifications@mailscore.app",
    "bulk_from": "bulk@mailscore.app",
    "configuration_set": "mail-score-production"
}', false),

('smtp_development', '{
    "service": "smtp",
    "host": "localhost",
    "port": 1025,
    "secure": false,
    "auth": {
        "user": "",
        "pass": ""
    },
    "default_from": "dev@localhost",
    "notification_from": "notifications@localhost",
    "bulk_from": "bulk@localhost"
}', false)

ON CONFLICT (config_name) DO NOTHING;

-- Create initial admin user settings (these would typically be created through the application)
-- This is just for reference - actual user creation should go through Supabase Auth

-- Insert webhook configurations for external integrations
INSERT INTO system_config (key, value, description) VALUES
('webhook_endpoints', '{
    "score_calculated": {
        "enabled": false,
        "url": "https://your-app.com/webhooks/score-calculated",
        "secret": "REPLACE_WITH_WEBHOOK_SECRET",
        "retry_attempts": 3,
        "timeout_seconds": 30
    },
    "job_completed": {
        "enabled": false,
        "url": "https://your-app.com/webhooks/job-completed",
        "secret": "REPLACE_WITH_WEBHOOK_SECRET",
        "retry_attempts": 3,
        "timeout_seconds": 30
    },
    "file_processed": {
        "enabled": false,
        "url": "https://your-app.com/webhooks/file-processed",
        "secret": "REPLACE_WITH_WEBHOOK_SECRET",
        "retry_attempts": 3,
        "timeout_seconds": 30
    }
}', 'External webhook configurations'),

('monitoring_settings', '{
    "health_check_interval_seconds": 60,
    "metric_collection_interval_seconds": 300,
    "alert_thresholds": {
        "high_error_rate": 0.05,
        "high_latency_ms": 2000,
        "low_uptime": 0.99,
        "storage_usage_percent": 90
    },
    "notification_channels": {
        "email": "alerts@mailscore.app",
        "slack_webhook": "",
        "pagerduty_key": ""
    }
}', 'System monitoring and alerting'),

('security_settings', '{
    "password_policy": {
        "min_length": 8,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_numbers": true,
        "require_symbols": false,
        "max_age_days": 90
    },
    "session_policy": {
        "max_session_duration_hours": 24,
        "idle_timeout_minutes": 60,
        "require_mfa": false,
        "max_concurrent_sessions": 3
    },
    "api_security": {
        "rate_limiting_enabled": true,
        "cors_enabled": true,
        "allowed_origins": ["https://mailscore.app", "https://www.mailscore.app"],
        "api_key_rotation_days": 30
    }
}', 'Security policies and settings')

ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Insert default scoring criteria templates
INSERT INTO system_config (key, value, description) VALUES
('default_email_scoring_criteria', '{
    "content_quality_weight": 0.30,
    "relevance_weight": 0.25,
    "engagement_potential_weight": 0.20,
    "technical_factors_weight": 0.15,
    "sender_reputation_weight": 0.10,
    "factors": {
        "content_quality": {
            "text_length": {"min": 50, "max": 2000, "optimal": 500},
            "readability": {"min_score": 60, "target_score": 80},
            "structure": {"has_paragraphs": true, "has_headers": false},
            "spelling_grammar": {"error_threshold": 0.02}
        },
        "relevance": {
            "keyword_density": {"min": 0.01, "max": 0.05},
            "topic_alignment": {"threshold": 0.7},
            "context_match": {"weight": 0.8}
        },
        "engagement": {
            "call_to_action": {"required": true, "position": "bottom"},
            "personalization": {"name": 0.3, "context": 0.7},
            "urgency_indicators": {"max_count": 2}
        }
    }
}', 'Default email scoring criteria and weights'),

('default_matching_scoring_criteria', '{
    "exact_match_weight": 0.40,
    "partial_match_weight": 0.25,
    "context_similarity_weight": 0.20,
    "temporal_relevance_weight": 0.10,
    "user_preference_weight": 0.05,
    "thresholds": {
        "exact_match": {"similarity": 0.95},
        "partial_match": {"similarity": 0.70},
        "context_similarity": {"similarity": 0.60},
        "temporal_decay": {"half_life_days": 30}
    }
}', 'Default matching scoring criteria and weights')

ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();