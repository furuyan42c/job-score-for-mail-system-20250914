-- T074: Deployment Migration - Database Functions
-- Create database functions for real-time operations

-- Function to execute SQL queries (for edge functions)
CREATE OR REPLACE FUNCTION execute_sql(query TEXT, params JSONB DEFAULT '{}')
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result JSONB;
    query_text TEXT;
BEGIN
    -- Security check: only allow service role
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: execute_sql requires service role';
    END IF;

    -- Simple parameter replacement (basic implementation)
    query_text := query;

    -- Execute the query and return results as JSONB
    EXECUTE 'SELECT array_to_json(array_agg(row_to_json(t))) FROM (' || query_text || ') t' INTO result;

    RETURN COALESCE(result, '[]'::JSONB);
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Query execution failed: %', SQLERRM;
END;
$$;

-- Function to create background job
CREATE OR REPLACE FUNCTION create_background_job(
    p_job_type TEXT,
    p_data JSONB,
    p_user_id UUID DEFAULT NULL,
    p_priority INTEGER DEFAULT 5
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    job_id UUID;
BEGIN
    INSERT INTO background_jobs (job_type, data, user_id, priority)
    VALUES (p_job_type, p_data, p_user_id, p_priority)
    RETURNING id INTO job_id;

    RETURN job_id;
END;
$$;

-- Function to update job status
CREATE OR REPLACE FUNCTION update_job_status(
    p_job_id UUID,
    p_status TEXT,
    p_metadata JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE background_jobs
    SET
        status = p_status,
        metadata = COALESCE(p_metadata, metadata),
        error_message = COALESCE(p_error_message, error_message),
        started_at = CASE WHEN p_status = 'processing' AND started_at IS NULL THEN NOW() ELSE started_at END,
        completed_at = CASE WHEN p_status IN ('completed', 'failed') THEN NOW() ELSE completed_at END,
        updated_at = NOW()
    WHERE id = p_job_id;

    RETURN FOUND;
END;
$$;

-- Function to cleanup expired files
CREATE OR REPLACE FUNCTION cleanup_expired_files()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    cleanup_count INTEGER := 0;
    expired_file RECORD;
BEGIN
    -- Only service role can run cleanup
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: cleanup requires service role';
    END IF;

    FOR expired_file IN
        SELECT file_id, bucket_name, storage_path
        FROM file_metadata
        WHERE expires_at IS NOT NULL AND expires_at < NOW()
    LOOP
        -- Delete from storage (this would need to be handled by application)
        -- For now, just mark as expired in metadata
        UPDATE file_metadata
        SET metadata = jsonb_set(metadata, '{expired}', 'true'::jsonb)
        WHERE file_id = expired_file.file_id;

        cleanup_count := cleanup_count + 1;
    END LOOP;

    RETURN cleanup_count;
END;
$$;

-- Function to get user file statistics
CREATE OR REPLACE FUNCTION get_user_file_stats(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    stats JSONB;
BEGIN
    -- Check if user can access their own stats
    IF auth.uid() != p_user_id AND auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: can only view own file statistics';
    END IF;

    SELECT jsonb_build_object(
        'total_files', COUNT(*),
        'total_size_bytes', COALESCE(SUM(size_bytes), 0),
        'files_by_type', jsonb_object_agg(file_type, type_count),
        'average_file_size', COALESCE(AVG(size_bytes), 0),
        'oldest_file', MIN(upload_time),
        'newest_file', MAX(upload_time)
    ) INTO stats
    FROM (
        SELECT
            file_type,
            size_bytes,
            upload_time,
            COUNT(*) OVER (PARTITION BY file_type) as type_count
        FROM file_metadata
        WHERE user_id = p_user_id
    ) file_stats;

    RETURN COALESCE(stats, '{}'::JSONB);
END;
$$;

-- Function to calculate performance metrics summary
CREATE OR REPLACE FUNCTION get_performance_summary(
    p_entity_type TEXT DEFAULT NULL,
    p_hours_back INTEGER DEFAULT 24
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    summary JSONB;
BEGIN
    SELECT jsonb_build_object(
        'period_hours', p_hours_back,
        'entity_type', COALESCE(p_entity_type, 'all'),
        'metrics', jsonb_build_object(
            'avg_latency_ms', COALESCE(AVG(latency_ms), 0),
            'avg_throughput', COALESCE(AVG(throughput), 0),
            'avg_accuracy', COALESCE(AVG(accuracy), 0),
            'avg_uptime', COALESCE(AVG(uptime), 0),
            'avg_efficiency', COALESCE(AVG(efficiency), 0)
        ),
        'total_records', COUNT(*),
        'time_range', jsonb_build_object(
            'from', MIN(recorded_at),
            'to', MAX(recorded_at)
        )
    ) INTO summary
    FROM performance_metrics
    WHERE recorded_at >= NOW() - (p_hours_back || ' hours')::INTERVAL
      AND (p_entity_type IS NULL OR entity_type = p_entity_type);

    RETURN COALESCE(summary, '{}'::JSONB);
END;
$$;

-- Function to get score calculation statistics
CREATE OR REPLACE FUNCTION get_score_stats(
    p_user_id UUID DEFAULT NULL,
    p_calculation_type TEXT DEFAULT NULL,
    p_days_back INTEGER DEFAULT 30
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    stats JSONB;
BEGIN
    -- Security check
    IF p_user_id IS NOT NULL AND auth.uid() != p_user_id AND auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: can only view own score statistics';
    END IF;

    SELECT jsonb_build_object(
        'period_days', p_days_back,
        'user_id', p_user_id,
        'calculation_type', p_calculation_type,
        'statistics', jsonb_build_object(
            'total_calculations', COUNT(*),
            'avg_overall_score', AVG((scores->>'overall_score')::NUMERIC),
            'avg_confidence', AVG(confidence),
            'avg_processing_time_ms', AVG(processing_time_ms),
            'calculations_by_type', jsonb_object_agg(calculation_type, type_count)
        ),
        'score_distribution', jsonb_build_object(
            'min_score', MIN((scores->>'overall_score')::NUMERIC),
            'max_score', MAX((scores->>'overall_score')::NUMERIC),
            'median_score', PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (scores->>'overall_score')::NUMERIC)
        )
    ) INTO stats
    FROM (
        SELECT
            calculation_type,
            scores,
            confidence,
            processing_time_ms,
            COUNT(*) OVER (PARTITION BY calculation_type) as type_count
        FROM score_calculations
        WHERE calculated_at >= NOW() - (p_days_back || ' days')::INTERVAL
          AND (p_user_id IS NULL OR user_id = p_user_id)
          AND (p_calculation_type IS NULL OR calculation_type = p_calculation_type)
    ) calc_stats;

    RETURN COALESCE(stats, '{}'::JSONB);
END;
$$;

-- Function to process job queue
CREATE OR REPLACE FUNCTION process_job_queue(p_limit INTEGER DEFAULT 10)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    processed_jobs JSONB := '[]'::JSONB;
    job_record RECORD;
    job_count INTEGER := 0;
BEGIN
    -- Only service role can process jobs
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: job processing requires service role';
    END IF;

    FOR job_record IN
        SELECT id, job_type, data, user_id, priority
        FROM background_jobs
        WHERE status = 'pending'
          AND (retry_count < max_retries OR retry_count IS NULL)
        ORDER BY priority ASC, created_at ASC
        LIMIT p_limit
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Mark job as processing
        UPDATE background_jobs
        SET status = 'processing', started_at = NOW(), updated_at = NOW()
        WHERE id = job_record.id;

        -- Add to processed jobs list
        processed_jobs := processed_jobs || jsonb_build_object(
            'job_id', job_record.id,
            'job_type', job_record.job_type,
            'user_id', job_record.user_id,
            'priority', job_record.priority
        );

        job_count := job_count + 1;
    END LOOP;

    RETURN jsonb_build_object(
        'processed_count', job_count,
        'jobs', processed_jobs
    );
END;
$$;

-- Function to clean old logs and data
CREATE OR REPLACE FUNCTION cleanup_old_data(p_days_to_keep INTEGER DEFAULT 90)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    cleanup_stats JSONB;
    cutoff_date TIMESTAMPTZ;
    deleted_jobs INTEGER;
    deleted_logs INTEGER;
    deleted_metrics INTEGER;
BEGIN
    -- Only service role can run cleanup
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Access denied: cleanup requires service role';
    END IF;

    cutoff_date := NOW() - (p_days_to_keep || ' days')::INTERVAL;

    -- Delete old completed/failed background jobs
    DELETE FROM background_jobs
    WHERE status IN ('completed', 'failed')
      AND completed_at < cutoff_date;
    GET DIAGNOSTICS deleted_jobs = ROW_COUNT;

    -- Delete old email logs
    DELETE FROM email_logs
    WHERE sent_at < cutoff_date;
    GET DIAGNOSTICS deleted_logs = ROW_COUNT;

    -- Delete old performance metrics
    DELETE FROM performance_metrics
    WHERE recorded_at < cutoff_date;
    GET DIAGNOSTICS deleted_metrics = ROW_COUNT;

    cleanup_stats := jsonb_build_object(
        'cutoff_date', cutoff_date,
        'days_kept', p_days_to_keep,
        'deleted_background_jobs', deleted_jobs,
        'deleted_email_logs', deleted_logs,
        'deleted_performance_metrics', deleted_metrics,
        'cleanup_completed_at', NOW()
    );

    RETURN cleanup_stats;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION execute_sql TO service_role;
GRANT EXECUTE ON FUNCTION create_background_job TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION update_job_status TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_files TO service_role;
GRANT EXECUTE ON FUNCTION get_user_file_stats TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_performance_summary TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_score_stats TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION process_job_queue TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data TO service_role;