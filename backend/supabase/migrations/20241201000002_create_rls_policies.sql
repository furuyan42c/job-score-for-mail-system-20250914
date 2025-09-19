-- T074: Deployment Migration - Row Level Security Policies
-- Create RLS policies for all real-time tables

-- Enable RLS on all tables
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE score_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_imports ENABLE ROW LEVEL SECURITY;

-- Background jobs policies
CREATE POLICY "Users can view their own background jobs" ON background_jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create background jobs" ON background_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own background jobs" ON background_jobs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all background jobs" ON background_jobs
    FOR ALL USING (auth.role() = 'service_role');

-- Email logs policies
CREATE POLICY "Users can view their own email logs" ON email_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all email logs" ON email_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Score calculations policies
CREATE POLICY "Users can view their own score calculations" ON score_calculations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create score calculations" ON score_calculations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can manage all score calculations" ON score_calculations
    FOR ALL USING (auth.role() = 'service_role');

-- File metadata policies
CREATE POLICY "Users can view their own file metadata" ON file_metadata
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create file metadata" ON file_metadata
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own file metadata" ON file_metadata
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own file metadata" ON file_metadata
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all file metadata" ON file_metadata
    FOR ALL USING (auth.role() = 'service_role');

-- Email config policies (admin only)
CREATE POLICY "Only service role can access email config" ON email_config
    FOR ALL USING (auth.role() = 'service_role');

-- Email templates policies
CREATE POLICY "All authenticated users can view active email templates" ON email_templates
    FOR SELECT USING (auth.role() = 'authenticated' AND active = true);

CREATE POLICY "Service role can manage all email templates" ON email_templates
    FOR ALL USING (auth.role() = 'service_role');

-- System config policies (admin only)
CREATE POLICY "Only service role can access system config" ON system_config
    FOR ALL USING (auth.role() = 'service_role');

-- Performance metrics policies
CREATE POLICY "Service role can manage all performance metrics" ON performance_metrics
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Authenticated users can view performance metrics" ON performance_metrics
    FOR SELECT USING (auth.role() = 'authenticated');

-- Data imports policies
CREATE POLICY "Users can view their own data imports" ON data_imports
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create data imports" ON data_imports
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own data imports" ON data_imports
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all data imports" ON data_imports
    FOR ALL USING (auth.role() = 'service_role');