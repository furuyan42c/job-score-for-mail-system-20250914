'use client';

import React, { useState, useEffect } from 'react';
import { EmailPreview } from './index';
import { EmailTemplate, User, EmailGenerationResponse, TestEmailResponse } from './types';

// Example implementation showing how to integrate EmailPreview with a real API
export function EmailPreviewExample() {
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load users on component mount
  useEffect(() => {
    loadUsers();
  }, []);

  // Load email template when user changes
  useEffect(() => {
    if (selectedUserId) {
      loadEmailTemplate(selectedUserId);
    }
  }, [selectedUserId]);

  const loadUsers = async () => {
    try {
      // Example API call to load users
      const response = await fetch('/api/users');
      if (!response.ok) throw new Error('Failed to load users');

      const userData = await response.json();
      setUsers(userData);

      if (userData.length > 0) {
        setSelectedUserId(userData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    }
  };

  const loadEmailTemplate = async (userId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Example API call to load email template
      const response = await fetch(`/api/email-template/${userId}`);
      if (!response.ok) throw new Error('Failed to load email template');

      const templateData = await response.json();
      setEmailTemplate(templateData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load email template');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserChange = (userId: string) => {
    setSelectedUserId(userId);
  };

  const handleRegenerateEmail = async () => {
    if (!selectedUserId) return;

    setIsLoading(true);
    setError(null);

    try {
      // Example API call to regenerate email
      const response = await fetch('/api/email-template/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: selectedUserId,
          force: true // Force regeneration even if recent template exists
        }),
      });

      if (!response.ok) throw new Error('Failed to regenerate email');

      const result: EmailGenerationResponse = await response.json();

      if (result.success && result.emailTemplate) {
        setEmailTemplate(result.emailTemplate);
      } else {
        throw new Error(result.error || 'Failed to regenerate email');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate email');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!emailTemplate) return;

    try {
      // Example API call to send test email
      const response = await fetch('/api/email-template/send-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: selectedUserId,
          emailTemplate,
          testEmailAddress: 'test@example.com' // Or get from user input
        }),
      });

      if (!response.ok) throw new Error('Failed to send test email');

      const result: TestEmailResponse = await response.json();

      if (result.success) {
        // Show success message
        alert('Test email sent successfully!');
      } else {
        throw new Error(result.error || 'Failed to send test email');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send test email');
    }
  };

  const handleSubjectChange = async (subject: string) => {
    if (!emailTemplate) return;

    try {
      // Example API call to update subject line
      const response = await fetch(`/api/email-template/${emailTemplate.id}/subject`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ subject }),
      });

      if (!response.ok) throw new Error('Failed to update subject');

      // Update local state
      setEmailTemplate(prev => prev ? { ...prev, subject } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update subject');
    }
  };

  return (
    <div className="h-screen">
      <EmailPreview
        emailTemplate={emailTemplate}
        users={users}
        selectedUserId={selectedUserId}
        onUserChange={handleUserChange}
        onRegenerateEmail={handleRegenerateEmail}
        onSendTestEmail={handleSendTestEmail}
        onSubjectChange={handleSubjectChange}
        isLoading={isLoading}
        error={error}
      />
    </div>
  );
}

// Example API route handlers (would go in separate files in a real app)

// /api/users - GET
export const getUsersHandler = async () => {
  // Example implementation
  const users: User[] = [
    {
      id: 'user_001',
      name: '田中太郎',
      email: 'tanaka@example.com',
      location: '東京都渋谷区',
      preferences: {
        occupations: ['エンジニア', 'プログラマー'],
        locations: ['東京都', '神奈川県'],
        salaryRange: { min: 4000, max: 8000 },
        employmentTypes: ['正社員', '契約社員']
      }
    },
    {
      id: 'user_002',
      name: '佐藤花子',
      email: 'sato@example.com',
      location: '大阪府大阪市',
      preferences: {
        occupations: ['デザイナー', 'クリエイター'],
        locations: ['大阪府', '京都府'],
        salaryRange: { min: 3000, max: 6000 },
        employmentTypes: ['正社員', 'フリーランス']
      }
    }
  ];

  return Response.json(users);
};

// /api/email-template/[userId] - GET
export const getEmailTemplateHandler = async (userId: string) => {
  // Example implementation - in real app, this would:
  // 1. Fetch user preferences from database
  // 2. Get job recommendations using ML model
  // 3. Generate email sections based on user history
  // 4. Use GPT-5 nano for content generation if needed
  // 5. Return complete email template

  // For now, return mock data
  const template: EmailTemplate = {
    id: `template_${userId}_${Date.now()}`,
    name: 'Daily Job Email',
    subject: '📧 ゲットバイト通信　${date}号 - ${totalJobs}件の新着求人',
    fromAddress: 'noreply@getbaito.com',
    sections: [], // Would be populated with real data
    metadata: {
      generatedAt: new Date().toISOString(),
      userId,
      userName: '田中太郎',
      userLocation: '東京都渋谷区',
      totalJobCount: 40,
      gptUsage: {
        model: 'gpt-5-nano',
        tokens: 1500,
        cost: 0.02
      },
      isFallbackTemplate: false,
      deliveryDate: new Date().toISOString().split('T')[0],
      templateVersion: '2.1.0'
    }
  };

  return Response.json(template);
};

// /api/email-template/generate - POST
export const generateEmailTemplateHandler = async (request: Request) => {
  const { userId, force } = await request.json();

  try {
    // Example implementation - in real app, this would:
    // 1. Check if recent template exists (unless force=true)
    // 2. Fetch fresh job data from database
    // 3. Run ML matching algorithms
    // 4. Generate personalized content with GPT-5 nano
    // 5. Create and save new template
    // 6. Return template with generation metadata

    const emailTemplate: EmailTemplate = {
      // ... generate new template
    } as EmailTemplate;

    const response: EmailGenerationResponse = {
      success: true,
      emailTemplate,
      fallbackUsed: false
    };

    return Response.json(response);
  } catch (error) {
    const response: EmailGenerationResponse = {
      success: false,
      error: error instanceof Error ? error.message : 'Generation failed'
    };

    return Response.json(response, { status: 500 });
  }
};

// /api/email-template/send-test - POST
export const sendTestEmailHandler = async (request: Request) => {
  const { userId, emailTemplate, testEmailAddress } = await request.json();

  try {
    // Example implementation - in real app, this would:
    // 1. Validate email template and test address
    // 2. Generate final HTML/text email content
    // 3. Send via email service (SES, SendGrid, etc.)
    // 4. Log send event for analytics
    // 5. Return success with message ID

    const response: TestEmailResponse = {
      success: true,
      messageId: `test_${Date.now()}`
    };

    return Response.json(response);
  } catch (error) {
    const response: TestEmailResponse = {
      success: false,
      error: error instanceof Error ? error.message : 'Send failed'
    };

    return Response.json(response, { status: 500 });
  }
};

// Example usage in a Next.js page
export default function EmailPreviewPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <EmailPreviewExample />
    </div>
  );
}