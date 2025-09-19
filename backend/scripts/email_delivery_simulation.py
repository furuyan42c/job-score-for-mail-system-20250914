#!/usr/bin/env python3
"""
T093-T096: Email Delivery Simulation Script

Combines:
- T093: Email generation test
- T094: Mailing list generation
- T095: Delivery simulation
- T096: Delivery result analysis

Usage:
    python scripts/email_delivery_simulation.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime, timedelta
import random
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


class EmailDeliverySimulator:
    def __init__(self):
        self.logger = setup_logging()
        self.emails_generated = 0
        self.deliveries_simulated = 0

    async def get_db_session(self) -> AsyncSession:
        database_url = 'sqlite+aiosqlite:///./app/database.db'
        engine = create_async_engine(database_url, echo=False)
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session_maker()

    async def create_email_tables(self, session: AsyncSession):
        """Create email-related tables for T093"""
        try:
            # Email templates table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT UNIQUE,
                    subject TEXT,
                    body TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Email queue table for T094
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS email_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    email TEXT,
                    subject TEXT,
                    body TEXT,
                    job_matches TEXT,
                    scheduled_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Delivery results table for T095-T096
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS delivery_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_queue_id INTEGER,
                    user_id TEXT,
                    delivery_status TEXT,
                    opened BOOLEAN DEFAULT FALSE,
                    clicked BOOLEAN DEFAULT FALSE,
                    bounce_type TEXT,
                    delivered_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP
                )
            """))

            await session.commit()
            self.logger.info("Created email tables")
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")

    async def generate_email_templates(self, session: AsyncSession):
        """T093: Generate email templates"""
        templates = [
            {
                'name': 'weekly_job_digest',
                'subject': '【週刊】あなたにおすすめの求人 {count}件',
                'body': '''
こんにちは、{user_name}様

今週のおすすめ求人をお届けします。

{job_list}

詳細はこちら: {detail_link}

配信停止: {unsubscribe_link}
'''
            },
            {
                'name': 'perfect_match',
                'subject': '【マッチ度{score}%】理想的な求人が見つかりました',
                'body': '''
{user_name}様

あなたの希望条件に非常に近い求人が見つかりました！

会社名: {company_name}
職種: {job_type}
給与: {salary}
勤務地: {location}
マッチ度: {score}%

今すぐ詳細を確認: {job_link}
'''
            }
        ]

        for template in templates:
            await session.execute(
                text("""
                    INSERT INTO email_templates (template_name, subject, body, created_at)
                    VALUES (:name, :subject, :body, :created_at)
                    ON CONFLICT (template_name) DO UPDATE SET
                        subject = :subject, body = :body
                """),
                {
                    'name': template['name'],
                    'subject': template['subject'],
                    'body': template['body'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        await session.commit()
        self.logger.info(f"Generated {len(templates)} email templates")

    async def generate_mailing_list(self, session: AsyncSession):
        """T094: Generate mailing list from user matches"""
        # Get users with matches
        result = await session.execute(text("""
            SELECT DISTINCT u.user_id, u.email, u.name,
                   COUNT(m.id) as match_count,
                   AVG(m.match_score) as avg_score,
                   GROUP_CONCAT(m.job_id || ':' || m.match_score, ',') as matches
            FROM users u
            JOIN user_job_matches m ON u.user_id = m.user_id
            WHERE m.match_score >= 60
            GROUP BY u.user_id
            HAVING match_count > 0
            LIMIT 50
        """))

        users = result.fetchall()

        for user in users:
            # Prepare email content
            subject = f"【週刊】あなたにおすすめの求人 {user[3]}件"
            body = f"""
こんにちは、{user[2]}様

今週のおすすめ求人 {user[3]}件をお届けします。
平均マッチ度: {user[4]:.1f}%

詳細はWebサイトでご確認ください。
"""

            # Add to email queue
            await session.execute(
                text("""
                    INSERT INTO email_queue (
                        user_id, email, subject, body, job_matches,
                        scheduled_at, status, created_at
                    ) VALUES (
                        :user_id, :email, :subject, :body, :matches,
                        :scheduled_at, 'pending', :created_at
                    )
                """),
                {
                    'user_id': user[0],
                    'email': user[1],
                    'subject': subject,
                    'body': body,
                    'matches': user[5],
                    'scheduled_at': (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            self.emails_generated += 1

        await session.commit()
        self.logger.info(f"Generated mailing list with {self.emails_generated} emails")

    async def simulate_delivery(self, session: AsyncSession):
        """T095: Simulate email delivery"""
        # Get pending emails
        result = await session.execute(text("""
            SELECT id, user_id, email FROM email_queue
            WHERE status = 'pending'
        """))

        emails = result.fetchall()

        for email_id, user_id, email_addr in emails:
            # Simulate delivery outcomes
            rand = random.random()

            if rand < 0.85:  # 85% successful delivery
                delivery_status = 'delivered'
                opened = random.random() < 0.30  # 30% open rate
                clicked = opened and random.random() < 0.15  # 15% CTR of opened
                bounce_type = None
            elif rand < 0.95:  # 10% soft bounce
                delivery_status = 'soft_bounce'
                opened = False
                clicked = False
                bounce_type = random.choice(['mailbox_full', 'temporary_failure'])
            else:  # 5% hard bounce
                delivery_status = 'hard_bounce'
                opened = False
                clicked = False
                bounce_type = random.choice(['invalid_email', 'domain_not_found'])

            # Record delivery result
            await session.execute(
                text("""
                    INSERT INTO delivery_results (
                        email_queue_id, user_id, delivery_status,
                        opened, clicked, bounce_type,
                        delivered_at, opened_at, clicked_at
                    ) VALUES (
                        :email_id, :user_id, :status,
                        :opened, :clicked, :bounce_type,
                        :delivered_at, :opened_at, :clicked_at
                    )
                """),
                {
                    'email_id': email_id,
                    'user_id': user_id,
                    'status': delivery_status,
                    'opened': opened,
                    'clicked': clicked,
                    'bounce_type': bounce_type,
                    'delivered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if delivery_status == 'delivered' else None,
                    'opened_at': (datetime.now() + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S') if opened else None,
                    'clicked_at': (datetime.now() + timedelta(hours=random.randint(2, 48))).strftime('%Y-%m-%d %H:%M:%S') if clicked else None
                }
            )

            # Update email queue status
            await session.execute(
                text("UPDATE email_queue SET status = :status WHERE id = :id"),
                {'status': delivery_status, 'id': email_id}
            )

            self.deliveries_simulated += 1

        await session.commit()
        self.logger.info(f"Simulated {self.deliveries_simulated} email deliveries")

    async def analyze_results(self, session: AsyncSession):
        """T096: Analyze delivery results"""
        result = await session.execute(text("""
            SELECT
                COUNT(*) as total_sent,
                COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered,
                COUNT(CASE WHEN delivery_status = 'soft_bounce' THEN 1 END) as soft_bounces,
                COUNT(CASE WHEN delivery_status = 'hard_bounce' THEN 1 END) as hard_bounces,
                COUNT(CASE WHEN opened = 1 THEN 1 END) as opened,
                COUNT(CASE WHEN clicked = 1 THEN 1 END) as clicked
            FROM delivery_results
        """))

        stats = result.fetchone()

        if stats[0] > 0:
            print("\n📧 Email Delivery Analysis (T096):")
            print(f"  Total Emails Sent: {stats[0]}")
            print(f"  Successfully Delivered: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
            print(f"  Soft Bounces: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
            print(f"  Hard Bounces: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
            print(f"  Opened: {stats[4]} ({stats[4]/stats[1]*100:.1f}% of delivered)" if stats[1] > 0 else "  Opened: 0")
            print(f"  Clicked: {stats[5]} ({stats[5]/stats[4]*100:.1f}% of opened)" if stats[4] > 0 else "  Clicked: 0")

        return stats

    async def run_all_tasks(self):
        """Execute T093-T096 in sequence"""
        async with await self.get_db_session() as session:
            print("📧 T093: Generating email templates...")
            await self.create_email_tables(session)
            await self.generate_email_templates(session)

            print("📋 T094: Generating mailing list...")
            await self.generate_mailing_list(session)

            print("🚀 T095: Simulating email delivery...")
            await self.simulate_delivery(session)

            print("📊 T096: Analyzing delivery results...")
            stats = await self.analyze_results(session)

            return stats


async def main():
    simulator = EmailDeliverySimulator()

    print("🚀 Starting Email Delivery Simulation (T093-T096)")
    print("=" * 50)

    stats = await simulator.run_all_tasks()

    if stats and stats[0] > 0:
        print("\n✨ Email delivery simulation completed successfully!")
        print(f"   Generated: {simulator.emails_generated} emails")
        print(f"   Simulated: {simulator.deliveries_simulated} deliveries")
        sys.exit(0)
    else:
        print("\n❌ Email delivery simulation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())