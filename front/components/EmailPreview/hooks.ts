import { useState, useEffect, useCallback } from 'react';
import {
  EmailTemplate,
  User,
  PreviewMode,
  EmailGenerationResponse,
  TestEmailResponse
} from './types';
import {
  generateMockEmailTemplate,
  generateMockUsers,
  formatSubjectLine,
  generateEmailSubjectVariables
} from './utils';

// Custom hook for managing email preview state
export const useEmailPreview = (initialUserId?: string) => {
  const [users] = useState<User[]>(generateMockUsers());
  const [selectedUserId, setSelectedUserId] = useState<string>(
    initialUserId || users[0]?.id || ''
  );
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate | null>(null);
  const [previewMode, setPreviewMode] = useState<PreviewMode>('desktop');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);

  // Load initial email template
  useEffect(() => {
    if (selectedUserId) {
      setIsLoading(true);
      setError(null);

      // Simulate API call
      setTimeout(() => {
        try {
          const template = generateMockEmailTemplate(selectedUserId);
          setEmailTemplate(template);
        } catch (err) {
          setError('メールテンプレートの読み込みに失敗しました');
        } finally {
          setIsLoading(false);
        }
      }, 1000);
    }
  }, [selectedUserId]);

  // Regenerate email template
  const regenerateEmail = useCallback(async () => {
    if (!selectedUserId) return;

    setIsGenerating(true);
    setError(null);

    try {
      // Simulate API call to regenerate email
      await new Promise(resolve => setTimeout(resolve, 2000));

      const newTemplate = generateMockEmailTemplate(selectedUserId);
      setEmailTemplate(newTemplate);
    } catch (err) {
      setError('メールの再生成に失敗しました');
    } finally {
      setIsGenerating(false);
    }
  }, [selectedUserId]);

  // Send test email
  const sendTestEmail = useCallback(async (testEmailAddress?: string) => {
    if (!emailTemplate) return;

    setIsSendingTest(true);
    setError(null);

    try {
      // Simulate API call to send test email
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock successful response
      const response: TestEmailResponse = {
        success: true,
        messageId: `test_${Date.now()}`
      };

      if (response.success) {
        // Could show a success toast here
        console.log('Test email sent successfully:', response.messageId);
      } else {
        throw new Error(response.error || 'テストメールの送信に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'テストメールの送信に失敗しました');
    } finally {
      setIsSendingTest(false);
    }
  }, [emailTemplate]);

  // Update subject line
  const updateSubjectLine = useCallback((newSubject: string) => {
    if (!emailTemplate) return;

    setEmailTemplate(prev => prev ? {
      ...prev,
      subject: newSubject
    } : null);
  }, [emailTemplate]);

  // Get formatted subject line
  const getFormattedSubject = useCallback(() => {
    if (!emailTemplate) return '';

    const variables = generateEmailSubjectVariables(emailTemplate);
    return formatSubjectLine(emailTemplate.subject, variables);
  }, [emailTemplate]);

  // Get selected user
  const selectedUser = users.find(user => user.id === selectedUserId);

  return {
    // State
    users,
    selectedUserId,
    selectedUser,
    emailTemplate,
    previewMode,
    isLoading,
    error,
    isGenerating,
    isSendingTest,

    // Actions
    setSelectedUserId,
    setPreviewMode,
    regenerateEmail,
    sendTestEmail,
    updateSubjectLine,
    getFormattedSubject,

    // Computed values
    totalJobs: emailTemplate?.metadata.totalJobCount || 0,
    lastGenerated: emailTemplate?.metadata.generatedAt || null
  };
};

// Custom hook for device frame management
export const useDeviceFrame = () => {
  const [device, setDevice] = useState<'desktop' | 'mobile'>('desktop');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleDevice = useCallback(() => {
    setDevice(prev => prev === 'desktop' ? 'mobile' : 'desktop');
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev);
  }, []);

  return {
    device,
    isFullscreen,
    toggleDevice,
    toggleFullscreen,
    setDevice,
    setIsFullscreen
  };
};

// Custom hook for email content management
export const useEmailContent = (emailTemplate: EmailTemplate | null) => {
  const [editingSubject, setEditingSubject] = useState(false);
  const [subjectDraft, setSubjectDraft] = useState('');

  // Sync draft with template subject
  useEffect(() => {
    if (emailTemplate) {
      setSubjectDraft(emailTemplate.subject);
    }
  }, [emailTemplate]);

  const startEditingSubject = useCallback(() => {
    setEditingSubject(true);
  }, []);

  const cancelEditingSubject = useCallback(() => {
    setEditingSubject(false);
    if (emailTemplate) {
      setSubjectDraft(emailTemplate.subject);
    }
  }, [emailTemplate]);

  const saveSubjectChanges = useCallback((onSave: (subject: string) => void) => {
    onSave(subjectDraft);
    setEditingSubject(false);
  }, [subjectDraft]);

  return {
    editingSubject,
    subjectDraft,
    setSubjectDraft,
    startEditingSubject,
    cancelEditingSubject,
    saveSubjectChanges
  };
};

// Custom hook for managing email analytics/metadata
export const useEmailAnalytics = (emailTemplate: EmailTemplate | null) => {
  const [analytics, setAnalytics] = useState({
    estimatedReadTime: 0,
    totalCharacters: 0,
    totalWords: 0,
    linkCount: 0,
    imageCount: 0
  });

  useEffect(() => {
    if (!emailTemplate) return;

    // Calculate analytics
    let totalCharacters = 0;
    let totalWords = 0;
    let linkCount = 0;

    emailTemplate.sections.forEach(section => {
      totalCharacters += section.title.length;
      totalWords += section.title.split(' ').length;

      if (section.description) {
        totalCharacters += section.description.length;
        totalWords += section.description.split(' ').length;
      }

      section.jobs.forEach(job => {
        totalCharacters += job.title.length + job.companyName.length + job.location.length;
        totalWords += job.title.split(' ').length + job.companyName.split(' ').length + job.location.split(' ').length;
        linkCount += 1; // Apply URL

        if (job.description) {
          totalCharacters += job.description.length;
          totalWords += job.description.split(' ').length;
        }
      });
    });

    // Estimate read time (assuming 200 words per minute for Japanese)
    const estimatedReadTime = Math.ceil(totalWords / 200);

    setAnalytics({
      estimatedReadTime,
      totalCharacters,
      totalWords,
      linkCount,
      imageCount: emailTemplate.sections.reduce((sum, section) =>
        sum + section.jobs.filter(job => job.companyLogo).length, 0
      )
    });
  }, [emailTemplate]);

  return analytics;
};