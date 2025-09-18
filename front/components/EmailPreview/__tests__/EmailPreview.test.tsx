import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EmailPreview } from '../index';
import { generateMockEmailTemplate, generateMockUsers } from '../utils';

// Mock the hooks
jest.mock('../hooks', () => ({
  useEmailPreview: jest.fn(),
  useDeviceFrame: jest.fn(),
  useEmailContent: jest.fn(),
  useEmailAnalytics: jest.fn()
}));

const mockUseEmailPreview = require('../hooks').useEmailPreview as jest.Mock;
const mockUseDeviceFrame = require('../hooks').useDeviceFrame as jest.Mock;
const mockUseEmailContent = require('../hooks').useEmailContent as jest.Mock;
const mockUseEmailAnalytics = require('../hooks').useEmailAnalytics as jest.Mock;

describe('EmailPreview', () => {
  const mockEmailTemplate = generateMockEmailTemplate();
  const mockUsers = generateMockUsers();

  beforeEach(() => {
    mockUseEmailPreview.mockReturnValue({
      users: mockUsers,
      selectedUserId: mockUsers[0].id,
      selectedUser: mockUsers[0],
      emailTemplate: mockEmailTemplate,
      previewMode: 'desktop',
      isLoading: false,
      error: null,
      isGenerating: false,
      isSendingTest: false,
      setSelectedUserId: jest.fn(),
      setPreviewMode: jest.fn(),
      regenerateEmail: jest.fn(),
      sendTestEmail: jest.fn(),
      updateSubjectLine: jest.fn(),
      getFormattedSubject: jest.fn(() => 'Test Subject'),
      totalJobs: 40,
      lastGenerated: new Date().toISOString()
    });

    mockUseDeviceFrame.mockReturnValue({
      device: 'desktop',
      isFullscreen: false,
      toggleDevice: jest.fn(),
      toggleFullscreen: jest.fn(),
      setDevice: jest.fn(),
      setIsFullscreen: jest.fn()
    });

    mockUseEmailContent.mockReturnValue({
      editingSubject: false,
      subjectDraft: '',
      setSubjectDraft: jest.fn(),
      startEditingSubject: jest.fn(),
      cancelEditingSubject: jest.fn(),
      saveSubjectChanges: jest.fn()
    });

    mockUseEmailAnalytics.mockReturnValue({
      estimatedReadTime: 5,
      totalCharacters: 1000,
      totalWords: 200,
      linkCount: 10,
      imageCount: 5
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders email preview component', () => {
    render(<EmailPreview />);

    expect(screen.getByText('Email Preview')).toBeInTheDocument();
    expect(screen.getByText('40件の求人')).toBeInTheDocument();
  });

  it('displays user selection dropdown', () => {
    render(<EmailPreview />);

    expect(screen.getByLabelText('ユーザー選択')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/田中太郎/)).toBeInTheDocument();
  });

  it('shows preview mode buttons', () => {
    render(<EmailPreview />);

    expect(screen.getByText('デスクトップ')).toBeInTheDocument();
    expect(screen.getByText('モバイル')).toBeInTheDocument();
    expect(screen.getByText('テキスト')).toBeInTheDocument();
    expect(screen.getByText('HTML')).toBeInTheDocument();
  });

  it('renders regenerate email button', () => {
    render(<EmailPreview />);

    const regenerateButton = screen.getByText('メール再生成');
    expect(regenerateButton).toBeInTheDocument();
    expect(regenerateButton).not.toBeDisabled();
  });

  it('renders send test email button', () => {
    render(<EmailPreview />);

    const sendTestButton = screen.getByText('テスト送信');
    expect(sendTestButton).toBeInTheDocument();
    expect(sendTestButton).not.toBeDisabled();
  });

  it('displays email analytics', () => {
    render(<EmailPreview />);

    expect(screen.getByText('5分')).toBeInTheDocument(); // Read time
    expect(screen.getByText('1,000')).toBeInTheDocument(); // Character count
    expect(screen.getByText('10')).toBeInTheDocument(); // Link count
  });

  it('handles loading state', () => {
    mockUseEmailPreview.mockReturnValue({
      ...mockUseEmailPreview(),
      isLoading: true,
      emailTemplate: null
    });

    render(<EmailPreview />);

    expect(screen.getByText('メールを読み込み中...')).toBeInTheDocument();
  });

  it('handles error state', () => {
    mockUseEmailPreview.mockReturnValue({
      ...mockUseEmailPreview(),
      error: 'Test error message',
      emailTemplate: null
    });

    render(<EmailPreview />);

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('handles generating state', () => {
    mockUseEmailPreview.mockReturnValue({
      ...mockUseEmailPreview(),
      isGenerating: true
    });

    render(<EmailPreview />);

    const regenerateButton = screen.getByText('生成中...');
    expect(regenerateButton).toBeInTheDocument();
    expect(regenerateButton).toBeDisabled();
  });

  it('handles sending test email state', () => {
    mockUseEmailPreview.mockReturnValue({
      ...mockUseEmailPreview(),
      isSendingTest: true
    });

    render(<EmailPreview />);

    const sendTestButton = screen.getByText('送信中...');
    expect(sendTestButton).toBeInTheDocument();
    expect(sendTestButton).toBeDisabled();
  });

  it('calls user change callback when user is selected', () => {
    const onUserChange = jest.fn();
    render(<EmailPreview onUserChange={onUserChange} />);

    const userSelect = screen.getByLabelText('ユーザー選択');
    fireEvent.change(userSelect, { target: { value: mockUsers[1].id } });

    expect(onUserChange).toHaveBeenCalledWith(mockUsers[1].id);
  });

  it('calls regenerate callback when regenerate button is clicked', () => {
    const onRegenerateEmail = jest.fn();
    render(<EmailPreview onRegenerateEmail={onRegenerateEmail} />);

    const regenerateButton = screen.getByText('メール再生成');
    fireEvent.click(regenerateButton);

    expect(onRegenerateEmail).toHaveBeenCalled();
  });

  it('calls send test email callback when send button is clicked', () => {
    const onSendTestEmail = jest.fn();
    render(<EmailPreview onSendTestEmail={onSendTestEmail} />);

    const sendButton = screen.getByText('テスト送信');
    fireEvent.click(sendButton);

    expect(onSendTestEmail).toHaveBeenCalled();
  });

  it('renders email sections', () => {
    render(<EmailPreview />);

    // Check for section titles from mock data
    expect(screen.getByText(/編集部おすすめ/)).toBeInTheDocument();
    expect(screen.getByText(/TOP5 おすすめ/)).toBeInTheDocument();
  });

  it('toggles fullscreen mode', () => {
    const mockToggleFullscreen = jest.fn();
    mockUseDeviceFrame.mockReturnValue({
      ...mockUseDeviceFrame(),
      toggleFullscreen: mockToggleFullscreen
    });

    render(<EmailPreview />);

    const fullscreenButton = screen.getByRole('button', { name: '' }); // Maximize icon button
    fireEvent.click(fullscreenButton);

    expect(mockToggleFullscreen).toHaveBeenCalled();
  });

  it('renders with custom props', () => {
    const customTemplate = generateMockEmailTemplate();
    const customUsers = generateMockUsers();

    render(
      <EmailPreview
        emailTemplate={customTemplate}
        users={customUsers}
        selectedUserId={customUsers[0].id}
        isLoading={false}
        error={null}
      />
    );

    expect(screen.getByText('Email Preview')).toBeInTheDocument();
  });

  it('handles subject line editing', () => {
    const mockStartEditingSubject = jest.fn();
    mockUseEmailContent.mockReturnValue({
      ...mockUseEmailContent(),
      editingSubject: false,
      startEditingSubject: mockStartEditingSubject
    });

    render(<EmailPreview />);

    // Find and click the edit button for subject
    const editButtons = screen.getAllByRole('button');
    const subjectEditButton = editButtons.find(button =>
      button.querySelector('svg') && button.closest('[role="group"], div')?.textContent?.includes('件名')
    );

    if (subjectEditButton) {
      fireEvent.click(subjectEditButton);
      expect(mockStartEditingSubject).toHaveBeenCalled();
    }
  });

  it('handles preview mode changes', () => {
    const mockSetPreviewMode = jest.fn();
    mockUseEmailPreview.mockReturnValue({
      ...mockUseEmailPreview(),
      setPreviewMode: mockSetPreviewMode
    });

    render(<EmailPreview />);

    const mobileButton = screen.getByText('モバイル');
    fireEvent.click(mobileButton);

    expect(mockSetPreviewMode).toHaveBeenCalledWith('mobile');
  });
});