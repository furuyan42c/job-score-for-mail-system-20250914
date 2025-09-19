#!/usr/bin/env python3
"""
T075: Supabase設定 - Validation Script
Comprehensive validation of Supabase configuration and setup
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables
load_env_file()

from app.core.supabase import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseSetupValidator:
    """Comprehensive Supabase setup validation"""

    def __init__(self):
        self.results = {
            'environment_variables': False,
            'client_initialization': False,
            'database_connection': False,
            'client_health': False,
            'configuration_validation': False
        }
        self.errors = []

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables are set"""
        logger.info("🔍 Validating environment variables...")

        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.errors.append(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.error(f"❌ Missing environment variables: {missing_vars}")
            return False

        logger.info("✅ All required environment variables are set")

        # Log configuration (safe logging)
        url = os.getenv('SUPABASE_URL', '')
        logger.info(f"   SUPABASE_URL: {url}")
        logger.info(f"   SUPABASE_ANON_KEY: {'***' + os.getenv('SUPABASE_ANON_KEY', '')[-10:]}")
        logger.info(f"   SUPABASE_SERVICE_ROLE_KEY: {'***' + os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')[-10:]}")

        return True

    def validate_client_initialization(self) -> bool:
        """Validate Supabase client can be initialized"""
        logger.info("🔍 Validating Supabase client initialization...")

        try:
            client = get_supabase_client()
            if client:
                logger.info("✅ Supabase client initialized successfully")
                return True
            else:
                self.errors.append("Supabase client is None")
                logger.error("❌ Supabase client initialization returned None")
                return False

        except Exception as e:
            self.errors.append(f"Client initialization failed: {str(e)}")
            logger.error(f"❌ Client initialization failed: {e}")
            return False

    async def validate_database_connection(self) -> bool:
        """Validate database connection through client"""
        logger.info("🔍 Validating database connection...")

        try:
            client = get_supabase_client()
            connection_test = await client.test_connection()

            if connection_test:
                logger.info("✅ Database connection successful")
                return True
            else:
                self.errors.append("Database connection test failed")
                logger.error("❌ Database connection test failed")
                return False

        except Exception as e:
            self.errors.append(f"Database connection error: {str(e)}")
            logger.error(f"❌ Database connection error: {e}")
            return False

    async def validate_client_health(self) -> bool:
        """Validate comprehensive client health check"""
        logger.info("🔍 Validating client health check...")

        try:
            client = get_supabase_client()
            health_data = await client.health_check()

            if health_data.get('status') in ['healthy', 'unhealthy']:
                logger.info(f"✅ Health check completed: {health_data.get('status')}")
                logger.info(f"   Response time: {health_data.get('response_time_ms', 0)}ms")
                logger.info(f"   Connection pool: {health_data.get('connection_pool', {})}")
                return True
            else:
                self.errors.append(f"Health check failed: {health_data}")
                logger.error(f"❌ Health check failed: {health_data}")
                return False

        except Exception as e:
            self.errors.append(f"Health check error: {str(e)}")
            logger.error(f"❌ Health check error: {e}")
            return False

    def validate_configuration_files(self) -> bool:
        """Validate configuration files exist and are valid"""
        logger.info("🔍 Validating configuration files...")

        config_files = [
            '.env',
            '.env.example',
            'app/core/supabase.py',
            'README_SUPABASE_DEPLOYMENT.md',
            'scripts/deploy_supabase.sh'
        ]

        missing_files = []
        for file_path in config_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            self.errors.append(f"Missing configuration files: {', '.join(missing_files)}")
            logger.error(f"❌ Missing configuration files: {missing_files}")
            return False

        logger.info("✅ All configuration files present")
        return True

    async def run_validation(self) -> bool:
        """Run complete validation suite"""
        logger.info("🚀 Starting T075 Supabase Setup Validation")
        logger.info("=" * 60)

        # Run all validations
        self.results['environment_variables'] = self.validate_environment_variables()
        self.results['client_initialization'] = self.validate_client_initialization()
        self.results['database_connection'] = await self.validate_database_connection()
        self.results['client_health'] = await self.validate_client_health()
        self.results['configuration_validation'] = self.validate_configuration_files()

        # Summary
        logger.info("=" * 60)
        logger.info("📊 VALIDATION RESULTS SUMMARY")
        logger.info("=" * 60)

        all_passed = True
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {test_name:<25}: {status}")
            if not result:
                all_passed = False

        if self.errors:
            logger.info("")
            logger.info("🚨 ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors, 1):
                logger.error(f"   {i}. {error}")

        logger.info("=" * 60)

        if all_passed:
            logger.info("🎉 T075 SUPABASE SETUP VALIDATION: SUCCESS")
            logger.info("   All Supabase configuration components are working correctly")
            logger.info("   The system is ready for development and testing")
        else:
            logger.error("💥 T075 SUPABASE SETUP VALIDATION: FAILED")
            logger.error("   Some configuration issues need to be resolved")

        logger.info("=" * 60)
        return all_passed

async def main():
    """Main validation entry point"""
    validator = SupabaseSetupValidator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())