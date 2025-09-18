"""
Supabase Client Module
Task: T066 - Setup Supabase local development environment
"""

import os
from typing import Optional, Dict, Any, Tuple
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from functools import lru_cache
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings


# Custom exceptions for Supabase operations
class SupabaseConnectionError(Exception):
    """Raised when connection to Supabase fails"""
    pass


class SupabaseConfigurationError(Exception):
    """Raised when Supabase configuration is invalid or missing"""
    pass


class SupabaseQueryError(Exception):
    """Raised when a Supabase query fails"""
    pass


# Singleton pattern for Supabase client
_supabase_client: Optional[Client] = None
_connection_pool_stats = {
    'active_connections': 0,
    'idle_connections': 0,
    'max_connections': 100
}


@lru_cache(maxsize=1)
def get_supabase_client(force_new: bool = False) -> Client:
    """
    Get or create a singleton Supabase client instance

    Args:
        force_new: Force creation of new client instance

    Returns:
        Supabase client instance

    Raises:
        SupabaseConfigurationError: If required configuration is missing
        SupabaseConnectionError: If connection to Supabase fails
    """
    global _supabase_client

    # Validate configuration
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise SupabaseConfigurationError(
            "Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_ANON_KEY"
        )

    if _supabase_client is None or force_new:
        try:
            # Create client options for better control
            options = ClientOptions(
                postgrest_client_timeout=30,
                storage_client_timeout=30,
                flow_type="pkce"
            )

            # Create Supabase client
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_ANON_KEY,
                options=options
            )

            # Update connection pool stats
            _connection_pool_stats['active_connections'] += 1

        except Exception as e:
            raise SupabaseConnectionError(
                f"Failed to create Supabase client: {str(e)}"
            )

    return _supabase_client


def get_admin_supabase_client() -> Client:
    """
    Get Supabase client with service role (admin) key

    Returns:
        Supabase client with admin privileges

    Raises:
        SupabaseConfigurationError: If service role key is missing
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise SupabaseConfigurationError(
            "Missing SUPABASE_SERVICE_ROLE_KEY for admin operations"
        )

    try:
        options = ClientOptions(
            postgrest_client_timeout=30,
            storage_client_timeout=30,
            flow_type="pkce"
        )

        return create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            options=options
        )
    except Exception as e:
        raise SupabaseConnectionError(
            f"Failed to create admin Supabase client: {str(e)}"
        )


async def check_supabase_health() -> Tuple[bool, str]:
    """
    Check Supabase connection health

    Returns:
        Tuple of (is_healthy, message)
    """
    try:
        client = get_supabase_client()

        # Try to execute a simple query
        response = client.from_('_test_connection').select('test_value').execute()

        if response.data is not None:
            return True, "Supabase is connected and healthy"

        return False, "Supabase connection test failed"

    except Exception as e:
        return False, f"Supabase health check failed: {str(e)}"


def get_connection_pool_stats() -> Dict[str, Any]:
    """
    Get connection pool statistics

    Returns:
        Dictionary with connection pool stats
    """
    return _connection_pool_stats.copy()


class SupabaseTransaction:
    """
    Context manager for database transactions
    Note: Supabase doesn't natively support transactions via REST API,
    this is a placeholder for future PostgreSQL direct connection
    """

    def __init__(self, client: Client):
        self.client = client
        self.transaction_id = None

    async def __aenter__(self):
        # In a real implementation, this would start a transaction
        # For now, it's a pass-through
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # In a real implementation, this would commit or rollback
        # based on whether an exception occurred
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        """Commit the transaction"""
        pass

    async def rollback(self):
        """Rollback the transaction"""
        pass


@asynccontextmanager
async def begin_transaction(client: Client):
    """
    Begin a database transaction

    Args:
        client: Supabase client instance

    Yields:
        Transaction context
    """
    transaction = SupabaseTransaction(client)
    try:
        yield transaction
    finally:
        pass


# Utility functions for common operations
def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Execute a raw SQL query via Supabase RPC

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        Query results

    Raises:
        SupabaseQueryError: If query execution fails
    """
    try:
        client = get_supabase_client()
        response = client.rpc('execute_sql', {'query': query, 'params': params or {}}).execute()
        return response.data
    except Exception as e:
        raise SupabaseQueryError(f"Query execution failed: {str(e)}")


def get_table(table_name: str):
    """
    Get a table reference for query building

    Args:
        table_name: Name of the table

    Returns:
        Table query builder
    """
    client = get_supabase_client()
    return client.from_(table_name)


# Realtime subscription helpers
def subscribe_to_table(table_name: str, callback):
    """
    Subscribe to realtime changes on a table

    Args:
        table_name: Name of the table to subscribe to
        callback: Function to call when changes occur

    Returns:
        Subscription channel
    """
    client = get_supabase_client()
    channel = client.channel(f'public:{table_name}')
    channel.on('postgres_changes', event='*', schema='public', table=table_name, callback=callback)
    channel.subscribe()
    return channel


def unsubscribe_from_table(channel):
    """
    Unsubscribe from a realtime channel

    Args:
        channel: Channel to unsubscribe from
    """
    if channel:
        channel.unsubscribe()


# Storage helpers
def get_storage_bucket(bucket_name: str):
    """
    Get a storage bucket reference

    Args:
        bucket_name: Name of the storage bucket

    Returns:
        Storage bucket reference
    """
    client = get_supabase_client()
    return client.storage.from_(bucket_name)


def upload_file(bucket_name: str, file_path: str, file_data: bytes, content_type: str = 'application/octet-stream'):
    """
    Upload a file to Supabase storage

    Args:
        bucket_name: Name of the storage bucket
        file_path: Path where file will be stored
        file_data: File data as bytes
        content_type: MIME type of the file

    Returns:
        Upload response
    """
    bucket = get_storage_bucket(bucket_name)
    return bucket.upload(file_path, file_data, {'content-type': content_type})


def download_file(bucket_name: str, file_path: str) -> bytes:
    """
    Download a file from Supabase storage

    Args:
        bucket_name: Name of the storage bucket
        file_path: Path of the file to download

    Returns:
        File data as bytes
    """
    bucket = get_storage_bucket(bucket_name)
    return bucket.download(file_path)


def delete_file(bucket_name: str, file_path: str):
    """
    Delete a file from Supabase storage

    Args:
        bucket_name: Name of the storage bucket
        file_path: Path of the file to delete

    Returns:
        Delete response
    """
    bucket = get_storage_bucket(bucket_name)
    return bucket.remove([file_path])


# Auth helpers (placeholder for future implementation)
def get_auth_client():
    """
    Get the auth client for user management

    Returns:
        Auth client instance
    """
    client = get_supabase_client()
    return client.auth


# Export all public functions and classes
__all__ = [
    'get_supabase_client',
    'get_admin_supabase_client',
    'check_supabase_health',
    'get_connection_pool_stats',
    'begin_transaction',
    'SupabaseConnectionError',
    'SupabaseConfigurationError',
    'SupabaseQueryError',
    'execute_query',
    'get_table',
    'subscribe_to_table',
    'unsubscribe_from_table',
    'get_storage_bucket',
    'upload_file',
    'download_file',
    'delete_file',
    'get_auth_client'
]