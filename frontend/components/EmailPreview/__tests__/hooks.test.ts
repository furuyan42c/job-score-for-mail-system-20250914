import { renderHook, act } from '@testing-library/react';
import {
  useEmailPreview,
  useDeviceFrame,
  useEmailContent,
  useEmailAnalytics
} from '../hooks';
import { generateMockEmailTemplate } from '../utils';

// Mock the utils
jest.mock('../utils', () => ({
  ...jest.requireActual('../utils'),
  generateMockUsers: jest.fn(() => [
    {
      id: 'user1',
      name: 'Test User 1',
      email: 'test1@example.com',
      location: 'Tokyo',
      preferences: {
        occupations: ['Engineer'],
        locations: ['Tokyo'],
        salaryRange: { min: 3000, max: 5000 },
        employmentTypes: ['Full-time']
      }
    },
    {
      id: 'user2',
      name: 'Test User 2',
      email: 'test2@example.com',
      location: 'Osaka',
      preferences: {
        occupations: ['Designer'],
        locations: ['Osaka'],
        salaryRange: { min: 2500, max: 4500 },
        employmentTypes: ['Part-time']
      }
    }
  ]),
  generateMockEmailTemplate: jest.fn()
}));

const mockGenerateEmailTemplate = require('../utils').generateMockEmailTemplate as jest.Mock;

describe('EmailPreview Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGenerateEmailTemplate.mockReturnValue(generateMockEmailTemplate('user1'));
  });

  describe('useEmailPreview', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('initializes with correct default values', () => {
      const { result } = renderHook(() => useEmailPreview());

      expect(result.current.users).toHaveLength(2);
      expect(result.current.selectedUserId).toBe('user1');
      expect(result.current.previewMode).toBe('desktop');
      expect(result.current.isLoading).toBe(true); // Initially loading
      expect(result.current.error).toBe(null);
      expect(result.current.isGenerating).toBe(false);
      expect(result.current.isSendingTest).toBe(false);
    });

    it('uses provided initial user id', () => {
      const { result } = renderHook(() => useEmailPreview('user2'));

      expect(result.current.selectedUserId).toBe('user2');
    });

    it('loads email template after timeout', async () => {
      const { result } = renderHook(() => useEmailPreview());

      expect(result.current.isLoading).toBe(true);
      expect(result.current.emailTemplate).toBe(null);

      // Fast forward time
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.emailTemplate).toBeTruthy();
      expect(mockGenerateEmailTemplate).toHaveBeenCalledWith('user1');
    });

    it('changes selected user and reloads template', () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Change user
      act(() => {
        result.current.setSelectedUserId('user2');
      });

      expect(result.current.selectedUserId).toBe('user2');
      expect(result.current.isLoading).toBe(true);

      // Fast forward reload
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.isLoading).toBe(false);
      expect(mockGenerateEmailTemplate).toHaveBeenCalledWith('user2');
    });

    it('changes preview mode', () => {
      const { result } = renderHook(() => useEmailPreview());

      act(() => {
        result.current.setPreviewMode('mobile');
      });

      expect(result.current.previewMode).toBe('mobile');
    });

    it('regenerates email template', async () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.isGenerating).toBe(false);

      // Start regeneration
      act(() => {
        result.current.regenerateEmail();
      });

      expect(result.current.isGenerating).toBe(true);

      // Fast forward regeneration
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      expect(result.current.isGenerating).toBe(false);
      expect(mockGenerateEmailTemplate).toHaveBeenCalledTimes(2); // Initial + regenerate
    });

    it('sends test email', async () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.isSendingTest).toBe(false);

      // Start sending test email
      act(() => {
        result.current.sendTestEmail('test@example.com');
      });

      expect(result.current.isSendingTest).toBe(true);

      // Fast forward sending
      act(() => {
        jest.advanceTimersByTime(1500);
      });

      expect(result.current.isSendingTest).toBe(false);
    });

    it('updates subject line', () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      const newSubject = 'New Subject Line';

      act(() => {
        result.current.updateSubjectLine(newSubject);
      });

      expect(result.current.emailTemplate?.subject).toBe(newSubject);
    });

    it('gets formatted subject', () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      const formattedSubject = result.current.getFormattedSubject();

      expect(typeof formattedSubject).toBe('string');
      expect(formattedSubject.length).toBeGreaterThan(0);
    });

    it('calculates total jobs correctly', () => {
      const { result } = renderHook(() => useEmailPreview());

      // Fast forward initial load
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(typeof result.current.totalJobs).toBe('number');
      expect(result.current.totalJobs).toBeGreaterThan(0);
    });

    it('finds selected user correctly', () => {
      const { result } = renderHook(() => useEmailPreview());

      expect(result.current.selectedUser?.id).toBe('user1');
      expect(result.current.selectedUser?.name).toBe('Test User 1');
    });
  });

  describe('useDeviceFrame', () => {
    it('initializes with desktop device', () => {
      const { result } = renderHook(() => useDeviceFrame());

      expect(result.current.device).toBe('desktop');
      expect(result.current.isFullscreen).toBe(false);
    });

    it('toggles device between desktop and mobile', () => {
      const { result } = renderHook(() => useDeviceFrame());

      act(() => {
        result.current.toggleDevice();
      });

      expect(result.current.device).toBe('mobile');

      act(() => {
        result.current.toggleDevice();
      });

      expect(result.current.device).toBe('desktop');
    });

    it('toggles fullscreen mode', () => {
      const { result } = renderHook(() => useDeviceFrame());

      act(() => {
        result.current.toggleFullscreen();
      });

      expect(result.current.isFullscreen).toBe(true);

      act(() => {
        result.current.toggleFullscreen();
      });

      expect(result.current.isFullscreen).toBe(false);
    });

    it('sets device directly', () => {
      const { result } = renderHook(() => useDeviceFrame());

      act(() => {
        result.current.setDevice('mobile');
      });

      expect(result.current.device).toBe('mobile');
    });

    it('sets fullscreen directly', () => {
      const { result } = renderHook(() => useDeviceFrame());

      act(() => {
        result.current.setIsFullscreen(true);
      });

      expect(result.current.isFullscreen).toBe(true);
    });
  });

  describe('useEmailContent', () => {
    const mockEmailTemplate = generateMockEmailTemplate();

    it('initializes with correct default values', () => {
      const { result } = renderHook(() => useEmailContent(mockEmailTemplate));

      expect(result.current.editingSubject).toBe(false);
      expect(result.current.subjectDraft).toBe(mockEmailTemplate.subject);
    });

    it('syncs draft with template subject when template changes', () => {
      const { result, rerender } = renderHook(
        ({ template }) => useEmailContent(template),
        { initialProps: { template: mockEmailTemplate } }
      );

      const newTemplate = { ...mockEmailTemplate, subject: 'New Subject' };

      rerender({ template: newTemplate });

      expect(result.current.subjectDraft).toBe('New Subject');
    });

    it('starts editing subject', () => {
      const { result } = renderHook(() => useEmailContent(mockEmailTemplate));

      act(() => {
        result.current.startEditingSubject();
      });

      expect(result.current.editingSubject).toBe(true);
    });

    it('cancels editing subject', () => {
      const { result } = renderHook(() => useEmailContent(mockEmailTemplate));

      act(() => {
        result.current.startEditingSubject();
        result.current.setSubjectDraft('Modified Draft');
        result.current.cancelEditingSubject();
      });

      expect(result.current.editingSubject).toBe(false);
      expect(result.current.subjectDraft).toBe(mockEmailTemplate.subject);
    });

    it('saves subject changes', () => {
      const mockOnSave = jest.fn();
      const { result } = renderHook(() => useEmailContent(mockEmailTemplate));

      act(() => {
        result.current.startEditingSubject();
        result.current.setSubjectDraft('New Subject Draft');
        result.current.saveSubjectChanges(mockOnSave);
      });

      expect(mockOnSave).toHaveBeenCalledWith('New Subject Draft');
      expect(result.current.editingSubject).toBe(false);
    });

    it('handles null email template', () => {
      const { result } = renderHook(() => useEmailContent(null));

      expect(result.current.editingSubject).toBe(false);
      expect(result.current.subjectDraft).toBe('');

      act(() => {
        result.current.cancelEditingSubject();
      });

      expect(result.current.subjectDraft).toBe('');
    });
  });

  describe('useEmailAnalytics', () => {
    const mockEmailTemplate = generateMockEmailTemplate();

    it('calculates analytics for email template', () => {
      const { result } = renderHook(() => useEmailAnalytics(mockEmailTemplate));

      expect(result.current.estimatedReadTime).toBeGreaterThan(0);
      expect(result.current.totalCharacters).toBeGreaterThan(0);
      expect(result.current.totalWords).toBeGreaterThan(0);
      expect(result.current.linkCount).toBeGreaterThan(0);
      expect(result.current.imageCount).toBeGreaterThanOrEqual(0);
    });

    it('handles null email template', () => {
      const { result } = renderHook(() => useEmailAnalytics(null));

      expect(result.current.estimatedReadTime).toBe(0);
      expect(result.current.totalCharacters).toBe(0);
      expect(result.current.totalWords).toBe(0);
      expect(result.current.linkCount).toBe(0);
      expect(result.current.imageCount).toBe(0);
    });

    it('recalculates when template changes', () => {
      const { result, rerender } = renderHook(
        ({ template }) => useEmailAnalytics(template),
        { initialProps: { template: mockEmailTemplate } }
      );

      const initialCharacters = result.current.totalCharacters;

      const modifiedTemplate = {
        ...mockEmailTemplate,
        sections: mockEmailTemplate.sections.map(section => ({
          ...section,
          title: section.title + ' Additional Text'
        }))
      };

      rerender({ template: modifiedTemplate });

      expect(result.current.totalCharacters).toBeGreaterThan(initialCharacters);
    });

    it('counts links correctly based on jobs', () => {
      const { result } = renderHook(() => useEmailAnalytics(mockEmailTemplate));

      const expectedLinkCount = mockEmailTemplate.sections.reduce(
        (sum, section) => sum + section.jobs.length,
        0
      );

      expect(result.current.linkCount).toBe(expectedLinkCount);
    });

    it('counts images correctly based on company logos', () => {
      const templateWithLogos = {
        ...mockEmailTemplate,
        sections: mockEmailTemplate.sections.map(section => ({
          ...section,
          jobs: section.jobs.map(job => ({
            ...job,
            companyLogo: 'https://example.com/logo.png'
          }))
        }))
      };

      const { result } = renderHook(() => useEmailAnalytics(templateWithLogos));

      const expectedImageCount = templateWithLogos.sections.reduce(
        (sum, section) => sum + section.jobs.length,
        0
      );

      expect(result.current.imageCount).toBe(expectedImageCount);
    });
  });
});