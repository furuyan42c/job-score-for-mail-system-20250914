-- T074: Deployment Migration - Real-time Tables
-- Create tables for real-time functionality

-- Background jobs table
CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retrying')),
    user_id UUID REFERENCES auth.users(id),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    data JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email logs table
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_type VARCHAR(50) NOT NULL,
    recipients TEXT[] NOT NULL,
    subject TEXT NOT NULL,
    message_id VARCHAR(255),
    success BOOLEAN NOT NULL,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id)
);

-- Score calculations table
CREATE TABLE IF NOT EXISTS score_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    scores JSONB NOT NULL,
    breakdown JSONB,
    confidence DECIMAL(3,2),
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id)
);

-- File metadata table
CREATE TABLE IF NOT EXISTS file_metadata (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    bucket_name VARCHAR(100) NOT NULL,
    storage_path TEXT NOT NULL,
    upload_time TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id),
    checksum VARCHAR(64),
    tags TEXT[] DEFAULT '{}',
    expires_at TIMESTAMPTZ,
    download_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Email configuration table
CREATE TABLE IF NOT EXISTS email_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(100) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    notification_type VARCHAR(50),
    subject TEXT NOT NULL,
    content JSONB NOT NULL,
    default_from VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- System configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    throughput DECIMAL(10,2),
    accuracy DECIMAL(3,2),
    uptime DECIMAL(5,4),
    efficiency DECIMAL(3,2),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data imports table
CREATE TABLE IF NOT EXISTS data_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_type VARCHAR(50) NOT NULL,
    file_id UUID REFERENCES file_metadata(file_id),
    user_id UUID REFERENCES auth.users(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX idx_background_jobs_status ON background_jobs(status);
CREATE INDEX idx_background_jobs_user_id ON background_jobs(user_id);
CREATE INDEX idx_background_jobs_created_at ON background_jobs(created_at);
CREATE INDEX idx_background_jobs_job_type ON background_jobs(job_type);

CREATE INDEX idx_email_logs_user_id ON email_logs(user_id);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX idx_email_logs_email_type ON email_logs(email_type);

CREATE INDEX idx_score_calculations_entity ON score_calculations(entity_id, entity_type);
CREATE INDEX idx_score_calculations_user_id ON score_calculations(user_id);
CREATE INDEX idx_score_calculations_calculated_at ON score_calculations(calculated_at);

CREATE INDEX idx_file_metadata_user_id ON file_metadata(user_id);
CREATE INDEX idx_file_metadata_upload_time ON file_metadata(upload_time);
CREATE INDEX idx_file_metadata_file_type ON file_metadata(file_type);
CREATE INDEX idx_file_metadata_expires_at ON file_metadata(expires_at);

CREATE INDEX idx_performance_metrics_entity ON performance_metrics(entity_id, entity_type);
CREATE INDEX idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);

CREATE INDEX idx_data_imports_user_id ON data_imports(user_id);
CREATE INDEX idx_data_imports_status ON data_imports(status);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_background_jobs_updated_at
    BEFORE UPDATE ON background_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_config_updated_at
    BEFORE UPDATE ON email_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default configurations
INSERT INTO email_config (config_name, config, active) VALUES
('default_smtp', '{
    "service": "smtp",
    "host": "localhost",
    "port": 587,
    "secure": false,
    "default_from": "noreply@example.com",
    "notification_from": "notifications@example.com",
    "bulk_from": "bulk@example.com"
}', true)
ON CONFLICT (config_name) DO NOTHING;

INSERT INTO system_config (key, value, description) VALUES
('bulk_email_limits', '{
    "max_recipients": 1000,
    "batch_size": 100,
    "batch_delay": 1000
}', 'Bulk email sending limits'),
('realtime_limits', '{
    "max_connections": 1000,
    "max_subscriptions_per_user": 10,
    "message_rate_limit": 100
}', 'Real-time service limits'),
('storage_limits', '{
    "max_file_size": 104857600,
    "max_files_per_user": 1000,
    "allowed_extensions": [".csv", ".pdf", ".txt", ".png", ".jpg", ".jpeg"]
}', 'Storage service limits')
ON CONFLICT (key) DO NOTHING;

INSERT INTO email_templates (template_name, type, subject, content) VALUES
('notification_default', 'notification', '{{title}}', '{
    "html": "<h2>{{title}}</h2><p>{{message}}</p>",
    "text": "{{title}}\n\n{{message}}"
}'),
('job_completion', 'notification', 'Job {{job_id}} Completed', '{
    "html": "<h2>Job Completed</h2><p>Your job <strong>{{job_id}}</strong> has been completed successfully.</p><p>Status: {{status}}</p>",
    "text": "Job Completed\n\nYour job {{job_id}} has been completed successfully.\nStatus: {{status}}"
}'),
('score_notification', 'notification', 'Score Calculation Ready', '{
    "html": "<h2>Score Calculation Complete</h2><p>Your score calculation is ready:</p><ul><li>Overall Score: {{overall_score}}</li><li>Confidence: {{confidence}}%</li></ul>",
    "text": "Score Calculation Complete\n\nYour score calculation is ready:\n- Overall Score: {{overall_score}}\n- Confidence: {{confidence}}%"
}')
ON CONFLICT (template_name) DO NOTHING;