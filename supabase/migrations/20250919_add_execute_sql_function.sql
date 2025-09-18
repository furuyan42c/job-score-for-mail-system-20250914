-- T069 GREEN Phase: SQL function for safe query execution
-- This function allows the Edge Function to execute read-only SQL queries

CREATE OR REPLACE FUNCTION execute_sql_query(query_text TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
    record_count INTEGER;
BEGIN
    -- Security: Only allow SELECT statements
    IF UPPER(TRIM(query_text)) NOT LIKE 'SELECT%' THEN
        RAISE EXCEPTION 'Only SELECT queries are allowed';
    END IF;

    -- Additional security: Check for dangerous keywords
    IF UPPER(query_text) ~ '(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|TRUNCATE)' THEN
        RAISE EXCEPTION 'Query contains forbidden keywords';
    END IF;

    -- Limit query execution time (timeout after 30 seconds)
    SET statement_timeout = '30s';

    -- Execute the query and return results as JSON
    BEGIN
        EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query_text || ') t' INTO result;

        -- If no results, return empty array
        IF result IS NULL THEN
            result := '[]'::JSON;
        END IF;

        RETURN result;

    EXCEPTION
        WHEN OTHERS THEN
            -- Reset timeout
            RESET statement_timeout;
            RAISE EXCEPTION 'Query execution error: %', SQLERRM;
    END;

    -- Reset timeout
    RESET statement_timeout;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION execute_sql_query(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION execute_sql_query(TEXT) TO anon;

-- Create a simpler version for RPC calls that returns the JSON directly
CREATE OR REPLACE FUNCTION execute_readonly_sql(sql_query TEXT)
RETURNS JSON AS $$
BEGIN
    RETURN execute_sql_query(sql_query);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION execute_readonly_sql(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION execute_readonly_sql(TEXT) TO anon;