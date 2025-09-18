-- =============================================================================
-- Initial Supabase Migration
-- Task: T066 - Setup Supabase local development environment
-- Description: Initialize database with required extensions and base configuration
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Text similarity
CREATE EXTENSION IF NOT EXISTS "vector";         -- Vector operations for AI/ML
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance tracking

-- =============================================================================
-- Create schemas for better organization
-- =============================================================================

-- Schema for application business logic
CREATE SCHEMA IF NOT EXISTS app;
COMMENT ON SCHEMA app IS 'Application business logic and tables';

-- Schema for authentication and user management
CREATE SCHEMA IF NOT EXISTS auth_app;
COMMENT ON SCHEMA auth_app IS 'Application-specific authentication extensions';

-- Schema for analytics and reporting
CREATE SCHEMA IF NOT EXISTS analytics;
COMMENT ON SCHEMA analytics IS 'Analytics and reporting tables';

-- Schema for background jobs and batch processing
CREATE SCHEMA IF NOT EXISTS batch;
COMMENT ON SCHEMA batch IS 'Batch processing and background job tables';

-- =============================================================================
-- Base configuration and settings
-- =============================================================================

-- Create configuration table
CREATE TABLE IF NOT EXISTS public.system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add useful indexes
CREATE INDEX IF NOT EXISTS idx_system_config_key ON public.system_config(key);

-- Insert default configuration
INSERT INTO public.system_config (key, value, description) VALUES
    ('app_version', '"1.0.0"', 'Application version'),
    ('maintenance_mode', 'false', 'System maintenance mode flag'),
    ('max_batch_size', '1000', 'Maximum batch processing size'),
    ('default_page_size', '50', 'Default pagination size'),
    ('enable_realtime', 'true', 'Enable realtime subscriptions'),
    ('enable_rls', 'true', 'Enable row level security')
ON CONFLICT (key) DO NOTHING;

-- =============================================================================
-- Create audit log table for tracking changes
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    user_id UUID,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON public.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON public.audit_log(created_at);

-- =============================================================================
-- Create health check function
-- =============================================================================

CREATE OR REPLACE FUNCTION public.health_check()
RETURNS TABLE (
    status TEXT,
    postgres_version TEXT,
    check_time TIMESTAMPTZ,
    database_name TEXT,
    is_superuser BOOLEAN,
    extensions JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        'healthy'::TEXT as status,
        version()::TEXT as postgres_version,
        NOW() as check_time,
        current_database()::TEXT as database_name,
        current_setting('is_superuser')::BOOLEAN as is_superuser,
        (
            SELECT jsonb_agg(extname ORDER BY extname)
            FROM pg_extension
            WHERE extname NOT IN ('plpgsql')
        ) as extensions;
END;
$$;

-- =============================================================================
-- Create test connection table (for connection verification)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public._test_connection (
    id SERIAL PRIMARY KEY,
    test_value INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert test record
INSERT INTO public._test_connection (test_value) VALUES (1);

-- =============================================================================
-- Setup RLS (Row Level Security) policies preparation
-- =============================================================================

-- Create a function to check if a user is authenticated
CREATE OR REPLACE FUNCTION public.is_authenticated()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.uid() IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get current user id
CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- Create performance monitoring functions
-- =============================================================================

-- Function to get database size
CREATE OR REPLACE FUNCTION public.get_database_size()
RETURNS TABLE (
    database_name TEXT,
    size_mb NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        current_database()::TEXT,
        ROUND(pg_database_size(current_database())::NUMERIC / 1024 / 1024, 2) as size_mb;
END;
$$;

-- Function to get table sizes
CREATE OR REPLACE FUNCTION public.get_table_sizes()
RETURNS TABLE (
    schema_name TEXT,
    table_name TEXT,
    size_mb NUMERIC,
    row_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname::TEXT,
        tablename::TEXT,
        ROUND(pg_total_relation_size(schemaname||'.'||tablename)::NUMERIC / 1024 / 1024, 2) as size_mb,
        n_live_tup as row_count
    FROM pg_stat_user_tables
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$;

-- =============================================================================
-- Create utility functions
-- =============================================================================

-- Function to generate random string
CREATE OR REPLACE FUNCTION public.generate_random_string(length INTEGER)
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::INTEGER, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to validate email format
CREATE OR REPLACE FUNCTION public.is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Create trigger function for updated_at timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION public.trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Create generic audit trigger function
-- =============================================================================

CREATE OR REPLACE FUNCTION public.trigger_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.audit_log (
        table_name,
        operation,
        user_id,
        record_id,
        old_data,
        new_data,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        auth.uid(),
        CASE
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        inet_client_addr(),
        current_setting('request.headers', true)::json->>'user-agent'
    );

    RETURN CASE
        WHEN TG_OP = 'DELETE' THEN OLD
        ELSE NEW
    END;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Setup permissions for anon and authenticated roles
-- =============================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT USAGE ON SCHEMA app TO authenticated;
GRANT USAGE ON SCHEMA analytics TO authenticated;

-- Grant execute on health check function to anon (for public health checks)
GRANT EXECUTE ON FUNCTION public.health_check() TO anon;

-- Grant execute on utility functions to authenticated users
GRANT EXECUTE ON FUNCTION public.is_authenticated() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_current_user_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.generate_random_string(INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_valid_email(TEXT) TO authenticated;

-- =============================================================================
-- Comments for documentation
-- =============================================================================

COMMENT ON TABLE public.system_config IS 'System-wide configuration settings';
COMMENT ON TABLE public.audit_log IS 'Audit log for tracking all database changes';
COMMENT ON TABLE public._test_connection IS 'Test table for connection verification';

COMMENT ON FUNCTION public.health_check() IS 'Database health check function';
COMMENT ON FUNCTION public.get_database_size() IS 'Get current database size in MB';
COMMENT ON FUNCTION public.get_table_sizes() IS 'Get sizes of all tables in the database';
COMMENT ON FUNCTION public.generate_random_string(INTEGER) IS 'Generate a random alphanumeric string';
COMMENT ON FUNCTION public.is_valid_email(TEXT) IS 'Validate email format';
COMMENT ON FUNCTION public.trigger_set_updated_at() IS 'Trigger function to auto-update updated_at timestamp';
COMMENT ON FUNCTION public.trigger_audit_log() IS 'Trigger function for audit logging';