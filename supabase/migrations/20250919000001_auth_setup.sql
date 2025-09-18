-- =============================================================================
-- T072: Supabase Auth Integration
-- Description: Setup authentication tables and functions
-- =============================================================================

-- Create profiles table for user metadata
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'manager')),
    department TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS public.user_preferences (
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE PRIMARY KEY,
    email_notifications BOOLEAN DEFAULT TRUE,
    realtime_updates BOOLEAN DEFAULT TRUE,
    preferred_language TEXT DEFAULT 'ja',
    theme TEXT DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    items_per_page INTEGER DEFAULT 50,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create sessions audit table
CREATE TABLE IF NOT EXISTS public.auth_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL CHECK (action IN ('login', 'logout', 'signup', 'password_reset', 'email_change')),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_auth_audit_user_id ON public.auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_action ON public.auth_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_auth_audit_created_at ON public.auth_audit_log(created_at);

-- =============================================================================
-- Authentication Functions
-- =============================================================================

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create profile entry for new user
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );

    -- Create default preferences
    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id);

    -- Log signup action
    INSERT INTO public.auth_audit_log (user_id, action, metadata)
    VALUES (
        NEW.id,
        'signup',
        jsonb_build_object(
            'email', NEW.email,
            'provider', NEW.raw_app_meta_data->>'provider'
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log authentication events
CREATE OR REPLACE FUNCTION public.log_auth_event(
    p_user_id UUID,
    p_action TEXT,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.auth_audit_log (
        user_id,
        action,
        ip_address,
        user_agent,
        metadata
    )
    VALUES (
        p_user_id,
        p_action,
        p_ip_address,
        p_user_agent,
        p_metadata
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user profile
CREATE OR REPLACE FUNCTION public.get_user_profile(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    email TEXT,
    full_name TEXT,
    role TEXT,
    department TEXT,
    avatar_url TEXT,
    preferences JSONB,
    created_at TIMESTAMPTZ
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.email,
        p.full_name,
        p.role,
        p.department,
        p.avatar_url,
        jsonb_build_object(
            'email_notifications', up.email_notifications,
            'realtime_updates', up.realtime_updates,
            'preferred_language', up.preferred_language,
            'theme', up.theme,
            'items_per_page', up.items_per_page
        ) as preferences,
        p.created_at
    FROM public.profiles p
    LEFT JOIN public.user_preferences up ON up.user_id = p.id
    WHERE p.id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has role
CREATE OR REPLACE FUNCTION public.user_has_role(p_user_id UUID, p_role TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_role TEXT;
BEGIN
    SELECT role INTO v_user_role
    FROM public.profiles
    WHERE id = p_user_id;

    IF p_role = 'user' THEN
        RETURN v_user_role IN ('user', 'manager', 'admin');
    ELSIF p_role = 'manager' THEN
        RETURN v_user_role IN ('manager', 'admin');
    ELSIF p_role = 'admin' THEN
        RETURN v_user_role = 'admin';
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user ID (for RLS policies)
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- Triggers
-- =============================================================================

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Update triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.trigger_set_updated_at();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION public.trigger_set_updated_at();

-- =============================================================================
-- Row Level Security (RLS) - Basic Setup for Auth
-- =============================================================================

-- Enable RLS on auth-related tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_audit_log ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view all profiles"
    ON public.profiles FOR SELECT
    USING (true);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- User preferences policies
CREATE POLICY "Users can view own preferences"
    ON public.user_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON public.user_preferences FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences"
    ON public.user_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Auth audit log policies (only admins can view)
CREATE POLICY "Only admins can view auth audit log"
    ON public.auth_audit_log FOR SELECT
    USING (public.user_has_role(auth.uid(), 'admin'));

-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant permissions to authenticated users
GRANT SELECT ON public.profiles TO authenticated;
GRANT UPDATE (full_name, department, avatar_url) ON public.profiles TO authenticated;

GRANT ALL ON public.user_preferences TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION public.get_user_profile(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.user_has_role(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_id() TO authenticated;

-- Admin-only functions
GRANT EXECUTE ON FUNCTION public.log_auth_event(UUID, TEXT, INET, TEXT, JSONB) TO authenticated;

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE public.profiles IS 'User profile information synchronized with auth.users';
COMMENT ON TABLE public.user_preferences IS 'User application preferences and settings';
COMMENT ON TABLE public.auth_audit_log IS 'Authentication event audit trail';

COMMENT ON FUNCTION public.handle_new_user() IS 'Automatically creates profile for new users';
COMMENT ON FUNCTION public.get_user_profile(UUID) IS 'Returns complete user profile with preferences';
COMMENT ON FUNCTION public.user_has_role(UUID, TEXT) IS 'Checks if user has specified role or higher';
COMMENT ON FUNCTION public.log_auth_event(UUID, TEXT, INET, TEXT, JSONB) IS 'Logs authentication events for audit';