/**
 * NextAuth.js API Route Handler
 * Handles authentication for the job matching system
 */

import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };