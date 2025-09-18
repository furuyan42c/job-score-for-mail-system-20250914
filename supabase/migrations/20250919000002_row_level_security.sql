-- =============================================================================
-- T073: Row Level Security Configuration
-- Description: Comprehensive RLS policies for all job matching system tables
-- =============================================================================

-- =============================================================================
-- SECTION 1: Enable RLS on All Tables
-- =============================================================================

-- Master Tables
ALTER TABLE prefecture_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE city_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE occupation_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment_type_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_master ENABLE ROW LEVEL SECURITY;

-- Core Tables
ALTER TABLE job_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE matching_results ENABLE ROW LEVEL SECURITY;

-- Scoring Tables
ALTER TABLE basic_scoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_scoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE personalized_scoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_scoring ENABLE ROW LEVEL SECURITY;

-- Batch Tables
ALTER TABLE batch_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;

-- Email Tables
ALTER TABLE email_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE section_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_generation_logs ENABLE ROW LEVEL SECURITY;

-- Statistics Tables
ALTER TABLE user_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE semrush_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- SECTION 2: Master Data Policies (Public Read)
-- =============================================================================

-- Prefecture Master: Everyone can read
CREATE POLICY "prefecture_master_read_all"
    ON prefecture_master FOR SELECT
    USING (true);

CREATE POLICY "prefecture_master_admin_write"
    ON prefecture_master FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- City Master: Everyone can read
CREATE POLICY "city_master_read_all"
    ON city_master FOR SELECT
    USING (true);

CREATE POLICY "city_master_admin_write"
    ON city_master FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- Occupation Master: Everyone can read
CREATE POLICY "occupation_master_read_all"
    ON occupation_master FOR SELECT
    USING (true);

CREATE POLICY "occupation_master_admin_write"
    ON occupation_master FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- Employment Type Master: Everyone can read
CREATE POLICY "employment_type_master_read_all"
    ON employment_type_master FOR SELECT
    USING (true);

CREATE POLICY "employment_type_master_admin_write"
    ON employment_type_master FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- Feature Master: Everyone can read
CREATE POLICY "feature_master_read_all"
    ON feature_master FOR SELECT
    USING (true);

CREATE POLICY "feature_master_admin_write"
    ON feature_master FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- =============================================================================
-- SECTION 3: Job Data Policies
-- =============================================================================

-- Job Data: Authenticated users can read
CREATE POLICY "job_data_authenticated_read"
    ON job_data FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Job Data: Managers and admins can insert
CREATE POLICY "job_data_manager_insert"
    ON job_data FOR INSERT
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Job Data: Managers and admins can update
CREATE POLICY "job_data_manager_update"
    ON job_data FOR UPDATE
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Job Data: Only admins can delete
CREATE POLICY "job_data_admin_delete"
    ON job_data FOR DELETE
    USING (public.user_has_role(auth.uid(), 'admin'));

-- =============================================================================
-- SECTION 4: User Action Policies
-- =============================================================================

-- User Actions: Users can read their own actions
CREATE POLICY "user_actions_own_read"
    ON user_actions FOR SELECT
    USING (auth.uid()::TEXT = user_id);

-- User Actions: Users can insert their own actions
CREATE POLICY "user_actions_own_insert"
    ON user_actions FOR INSERT
    WITH CHECK (auth.uid()::TEXT = user_id);

-- User Actions: Users can update their own actions
CREATE POLICY "user_actions_own_update"
    ON user_actions FOR UPDATE
    USING (auth.uid()::TEXT = user_id)
    WITH CHECK (auth.uid()::TEXT = user_id);

-- User Actions: Admins can view all
CREATE POLICY "user_actions_admin_all"
    ON user_actions FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- =============================================================================
-- SECTION 5: Matching Results Policies
-- =============================================================================

-- Matching Results: Users can read their own results
CREATE POLICY "matching_results_own_read"
    ON matching_results FOR SELECT
    USING (auth.uid()::TEXT = user_id);

-- Matching Results: System (via service role) can insert
-- Note: Matching is done by backend service, not directly by users
CREATE POLICY "matching_results_system_insert"
    ON matching_results FOR INSERT
    WITH CHECK (
        auth.uid() IS NOT NULL AND
        public.user_has_role(auth.uid(), 'manager')
    );

-- Matching Results: Admins can manage all
CREATE POLICY "matching_results_admin_all"
    ON matching_results FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- =============================================================================
-- SECTION 6: Scoring Tables Policies
-- =============================================================================

-- Basic Scoring: Authenticated users can read
CREATE POLICY "basic_scoring_authenticated_read"
    ON basic_scoring FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Basic Scoring: Managers can write
CREATE POLICY "basic_scoring_manager_write"
    ON basic_scoring FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- SEO Scoring: Authenticated users can read
CREATE POLICY "seo_scoring_authenticated_read"
    ON seo_scoring FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- SEO Scoring: Managers can write
CREATE POLICY "seo_scoring_manager_write"
    ON seo_scoring FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Personalized Scoring: Users can read their own scores
CREATE POLICY "personalized_scoring_own_read"
    ON personalized_scoring FOR SELECT
    USING (auth.uid()::TEXT = user_id);

-- Personalized Scoring: System can write
CREATE POLICY "personalized_scoring_system_write"
    ON personalized_scoring FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Keyword Scoring: Authenticated users can read
CREATE POLICY "keyword_scoring_authenticated_read"
    ON keyword_scoring FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Keyword Scoring: Managers can write
CREATE POLICY "keyword_scoring_manager_write"
    ON keyword_scoring FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- =============================================================================
-- SECTION 7: Batch Processing Policies
-- =============================================================================

-- Batch Jobs: Managers can view all
CREATE POLICY "batch_jobs_manager_read"
    ON batch_jobs FOR SELECT
    USING (public.user_has_role(auth.uid(), 'manager'));

-- Batch Jobs: Admins can manage
CREATE POLICY "batch_jobs_admin_write"
    ON batch_jobs FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- Processing Logs: Managers can view
CREATE POLICY "processing_logs_manager_read"
    ON processing_logs FOR SELECT
    USING (public.user_has_role(auth.uid(), 'manager'));

-- Processing Logs: System can write
CREATE POLICY "processing_logs_system_write"
    ON processing_logs FOR INSERT
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- =============================================================================
-- SECTION 8: Email Management Policies
-- =============================================================================

-- Email Sections: All authenticated users can read (configuration data)
CREATE POLICY "email_sections_authenticated_read"
    ON email_sections FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Email Sections: Only managers can write
CREATE POLICY "email_sections_manager_write"
    ON email_sections FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Section Jobs: Authenticated users can read
CREATE POLICY "section_jobs_authenticated_read"
    ON section_jobs FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Section Jobs: Managers can write
CREATE POLICY "section_jobs_manager_write"
    ON section_jobs FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- Email Generation Logs: Users can read their own (if user_id column exists)
-- Note: email_generation_logs table should have user_id for user-specific logs
CREATE POLICY "email_logs_authenticated_read"
    ON email_generation_logs FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Email Generation Logs: Managers can write
CREATE POLICY "email_logs_manager_write"
    ON email_generation_logs FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- =============================================================================
-- SECTION 9: Statistics Policies
-- =============================================================================

-- User Statistics: Users can read their own
CREATE POLICY "user_statistics_own_read"
    ON user_statistics FOR SELECT
    USING (auth.uid()::TEXT = user_id);

-- User Statistics: System can write
CREATE POLICY "user_statistics_system_write"
    ON user_statistics FOR ALL
    USING (public.user_has_role(auth.uid(), 'manager'))
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- SEMrush Keywords: Managers can read
CREATE POLICY "semrush_keywords_manager_read"
    ON semrush_keywords FOR SELECT
    USING (public.user_has_role(auth.uid(), 'manager'));

-- SEMrush Keywords: Admins can write
CREATE POLICY "semrush_keywords_admin_write"
    ON semrush_keywords FOR ALL
    USING (public.user_has_role(auth.uid(), 'admin'))
    WITH CHECK (public.user_has_role(auth.uid(), 'admin'));

-- System Metrics: Managers can read
CREATE POLICY "system_metrics_manager_read"
    ON system_metrics FOR SELECT
    USING (public.user_has_role(auth.uid(), 'manager'));

-- System Metrics: System can write
CREATE POLICY "system_metrics_system_write"
    ON system_metrics FOR INSERT
    WITH CHECK (public.user_has_role(auth.uid(), 'manager'));

-- =============================================================================
-- SECTION 10: Functions for RLS Support
-- =============================================================================

-- Function to check if current user owns a resource
CREATE OR REPLACE FUNCTION public.user_owns_resource(resource_user_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.uid()::TEXT = resource_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check read permissions for job data
CREATE OR REPLACE FUNCTION public.can_read_job(job_id BIGINT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Authenticated users can read any job
    RETURN auth.uid() IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check write permissions for job data
CREATE OR REPLACE FUNCTION public.can_write_job(job_id BIGINT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Managers and admins can write
    RETURN public.user_has_role(auth.uid(), 'manager');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- SECTION 11: Grant Permissions
-- =============================================================================

-- Grant basic table access to authenticated users
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;

-- Grant specific write permissions based on policies
GRANT INSERT, UPDATE ON user_actions TO authenticated;
GRANT INSERT, UPDATE ON user_preferences TO authenticated;

-- Grant execute on RLS support functions
GRANT EXECUTE ON FUNCTION public.user_owns_resource(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.can_read_job(BIGINT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.can_write_job(BIGINT) TO authenticated;

-- =============================================================================
-- SECTION 12: Bypass RLS for Service Role (Backend Operations)
-- =============================================================================

-- Create policies for service role to bypass RLS for backend operations
-- Note: Service role key should only be used server-side

-- System configuration: Service role can manage
CREATE POLICY "system_config_service_role"
    ON system_config FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Audit log: Service role can write
CREATE POLICY "audit_log_service_role"
    ON audit_log FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON POLICY "job_data_authenticated_read" ON job_data IS
    'Allow authenticated users to read all job data';

COMMENT ON POLICY "user_actions_own_read" ON user_actions IS
    'Users can only read their own action history';

COMMENT ON POLICY "matching_results_own_read" ON matching_results IS
    'Users can only see their own matching results';

COMMENT ON FUNCTION public.user_owns_resource(TEXT) IS
    'Check if current user owns a resource by user_id';

COMMENT ON FUNCTION public.can_read_job(BIGINT) IS
    'Check if current user can read a specific job';

COMMENT ON FUNCTION public.can_write_job(BIGINT) IS
    'Check if current user can write to a specific job';