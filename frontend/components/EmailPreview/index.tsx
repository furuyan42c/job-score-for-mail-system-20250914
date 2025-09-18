'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

import { EmailSection } from './EmailSection';
import { DeviceFrame } from './DeviceFrame';
import { EmailPreviewProps, PreviewMode } from './types';
import { useEmailPreview, useDeviceFrame, useEmailContent, useEmailAnalytics } from './hooks';
import { convertToPlainText, convertToHTMLSource } from './utils';

import {
  RefreshCw,
  Send,
  Edit,
  Check,
  X,
  Monitor,
  Smartphone,
  FileText,
  Code,
  User,
  Mail,
  Calendar,
  Clock,
  Zap,
  TrendingUp,
  Eye,
  Settings,
  Download,
  Share,
  Maximize,
  Minimize
} from 'lucide-react';

export const EmailPreview: React.FC<EmailPreviewProps> = ({
  emailTemplate: propEmailTemplate,
  users: propUsers,
  selectedUserId: propSelectedUserId,
  onUserChange,
  onRegenerateEmail,
  onSendTestEmail,
  onSubjectChange,
  isLoading: propIsLoading,
  error: propError
}) => {
  const {
    users,
    selectedUserId,
    selectedUser,
    emailTemplate,
    previewMode,
    isLoading,
    error,
    isGenerating,
    isSendingTest,
    setSelectedUserId,
    setPreviewMode,
    regenerateEmail,
    sendTestEmail,
    updateSubjectLine,
    getFormattedSubject,
    totalJobs,
    lastGenerated
  } = useEmailPreview(propSelectedUserId);

  const { device, isFullscreen, toggleDevice, toggleFullscreen } = useDeviceFrame();

  const {
    editingSubject,
    subjectDraft,
    setSubjectDraft,
    startEditingSubject,
    cancelEditingSubject,
    saveSubjectChanges
  } = useEmailContent(emailTemplate);

  const analytics = useEmailAnalytics(emailTemplate);

  // Use props if provided, otherwise use hook state
  const currentEmailTemplate = propEmailTemplate || emailTemplate;
  const currentUsers = propUsers || users;
  const currentSelectedUserId = propSelectedUserId || selectedUserId;
  const currentIsLoading = propIsLoading ?? isLoading;
  const currentError = propError || error;

  const handleUserChange = (userId: string) => {
    if (onUserChange) {
      onUserChange(userId);
    } else {
      setSelectedUserId(userId);
    }
  };

  const handleRegenerateEmail = () => {
    if (onRegenerateEmail) {
      onRegenerateEmail();
    } else {
      regenerateEmail();
    }
  };

  const handleSendTestEmail = () => {
    if (onSendTestEmail) {
      onSendTestEmail();
    } else {
      sendTestEmail();
    }
  };

  const handleSubjectChange = (newSubject: string) => {
    if (onSubjectChange) {
      onSubjectChange(newSubject);
    } else {
      updateSubjectLine(newSubject);
    }
  };

  const renderPreviewModeIcon = (mode: PreviewMode) => {
    switch (mode) {
      case 'desktop':
        return <Monitor className="h-4 w-4" />;
      case 'mobile':
        return <Smartphone className="h-4 w-4" />;
      case 'plaintext':
        return <FileText className="h-4 w-4" />;
      case 'html':
        return <Code className="h-4 w-4" />;
    }
  };

  const renderEmailContent = () => {
    if (!currentEmailTemplate) return null;

    switch (previewMode) {
      case 'plaintext':
        return (
          <div className="bg-gray-50 p-6 rounded-lg">
            <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed">
              {convertToPlainText(currentEmailTemplate)}
            </pre>
          </div>
        );

      case 'html':
        return (
          <div className="bg-gray-50 p-6 rounded-lg">
            <pre className="whitespace-pre-wrap font-mono text-xs text-gray-800 leading-relaxed overflow-x-auto">
              {convertToHTMLSource(currentEmailTemplate)}
            </pre>
          </div>
        );

      case 'desktop':
      case 'mobile':
        return (
          <DeviceFrame device={previewMode === 'mobile' ? 'mobile' : 'desktop'}>
            <div className={cn(
              'bg-white',
              previewMode === 'mobile' ? 'p-4' : 'p-8'
            )}>
              {/* Email Header */}
              <div className="mb-8 border-b border-gray-200 pb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="h-5 w-5 text-blue-600" />
                  <span className="text-sm text-gray-600">From: {currentEmailTemplate.fromAddress}</span>
                </div>
                <h1 className={cn(
                  'font-bold text-gray-900 mb-2',
                  previewMode === 'mobile' ? 'text-lg' : 'text-2xl'
                )}>
                  {getFormattedSubject()}
                </h1>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    <span>{currentEmailTemplate.metadata.userName}さん</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <span>{currentEmailTemplate.metadata.deliveryDate}</span>
                  </div>
                </div>
              </div>

              {/* Welcome Message */}
              <div className="mb-8 bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-gray-800">
                  {currentEmailTemplate.metadata.userName}さん、こんにちは！<br />
                  {currentEmailTemplate.metadata.userLocation}の求人情報を{totalJobs}件お届けします。
                </p>
              </div>

              {/* Email Sections */}
              <div className="space-y-8">
                {currentEmailTemplate.sections.map(section => (
                  <EmailSection
                    key={section.id}
                    section={section}
                    previewMode={previewMode}
                  />
                ))}
              </div>

              {/* Email Footer */}
              <div className="mt-12 pt-8 border-t border-gray-200 text-center">
                <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-600">
                  <p className="mb-2">
                    このメールは{currentEmailTemplate.metadata.gptUsage?.model || 'AI'}により生成されました
                  </p>
                  <p className="text-xs">
                    生成日時: {new Date(currentEmailTemplate.metadata.generatedAt).toLocaleString('ja-JP')}
                  </p>
                  {currentEmailTemplate.metadata.isFallbackTemplate && (
                    <Badge variant="outline" className="mt-2">
                      フォールバックテンプレート使用
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </DeviceFrame>
        );
    }
  };

  return (
    <div className={cn(
      'h-full flex flex-col bg-gray-50',
      isFullscreen && 'fixed inset-0 z-50'
    )}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900">Email Preview</h1>
            {currentEmailTemplate && (
              <Badge variant="outline">
                {totalJobs}件の求人
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleFullscreen}
            >
              {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* User Selection */}
          <div className="p-4 border-b border-gray-200">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ユーザー選択
            </label>
            <select
              value={currentSelectedUserId}
              onChange={(e) => handleUserChange(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md text-sm"
              disabled={currentIsLoading}
            >
              {currentUsers.map(user => (
                <option key={user.id} value={user.id}>
                  {user.name} ({user.location})
                </option>
              ))}
            </select>
          </div>

          {/* Subject Line Editing */}
          {currentEmailTemplate && (
            <div className="p-4 border-b border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                件名
              </label>
              {editingSubject ? (
                <div className="space-y-2">
                  <Input
                    value={subjectDraft}
                    onChange={(e) => setSubjectDraft(e.target.value)}
                    className="text-sm"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => saveSubjectChanges(handleSubjectChange)}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={cancelEditingSubject}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <div className="flex-1 text-sm text-gray-600 break-words">
                    {getFormattedSubject()}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={startEditingSubject}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Preview Mode Selection */}
          <div className="p-4 border-b border-gray-200">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              プレビューモード
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['desktop', 'mobile', 'plaintext', 'html'] as PreviewMode[]).map(mode => (
                <Button
                  key={mode}
                  variant={previewMode === mode ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPreviewMode(mode)}
                  className="justify-start"
                >
                  {renderPreviewModeIcon(mode)}
                  <span className="ml-2 text-xs">
                    {mode === 'desktop' ? 'デスクトップ' :
                     mode === 'mobile' ? 'モバイル' :
                     mode === 'plaintext' ? 'テキスト' : 'HTML'}
                  </span>
                </Button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="p-4 border-b border-gray-200 space-y-2">
            <Button
              onClick={handleRegenerateEmail}
              disabled={isGenerating || currentIsLoading}
              className="w-full"
              size="sm"
            >
              <RefreshCw className={cn('h-4 w-4 mr-2', isGenerating && 'animate-spin')} />
              {isGenerating ? '生成中...' : 'メール再生成'}
            </Button>

            <Button
              onClick={handleSendTestEmail}
              disabled={isSendingTest || !currentEmailTemplate}
              variant="outline"
              className="w-full"
              size="sm"
            >
              <Send className="h-4 w-4 mr-2" />
              {isSendingTest ? '送信中...' : 'テスト送信'}
            </Button>
          </div>

          {/* Email Analytics */}
          {currentEmailTemplate && (
            <div className="p-4 flex-1 overflow-hidden">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                メール情報
              </h3>
              <ScrollArea className="h-full">
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-blue-50 p-2 rounded">
                      <div className="flex items-center gap-1 text-blue-600 mb-1">
                        <Eye className="h-3 w-3" />
                        <span>読了時間</span>
                      </div>
                      <div className="font-semibold">{analytics.estimatedReadTime}分</div>
                    </div>

                    <div className="bg-green-50 p-2 rounded">
                      <div className="flex items-center gap-1 text-green-600 mb-1">
                        <TrendingUp className="h-3 w-3" />
                        <span>総文字数</span>
                      </div>
                      <div className="font-semibold">{analytics.totalCharacters.toLocaleString()}</div>
                    </div>

                    <div className="bg-orange-50 p-2 rounded">
                      <div className="flex items-center gap-1 text-orange-600 mb-1">
                        <Zap className="h-3 w-3" />
                        <span>リンク数</span>
                      </div>
                      <div className="font-semibold">{analytics.linkCount}</div>
                    </div>

                    <div className="bg-purple-50 p-2 rounded">
                      <div className="flex items-center gap-1 text-purple-600 mb-1">
                        <Clock className="h-3 w-3" />
                        <span>生成日時</span>
                      </div>
                      <div className="font-semibold text-xs">
                        {lastGenerated && new Date(lastGenerated).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  {/* GPT Usage */}
                  {currentEmailTemplate.metadata.gptUsage && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <h4 className="text-xs font-medium text-gray-700 mb-2">AI使用状況</h4>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div>モデル: {currentEmailTemplate.metadata.gptUsage.model}</div>
                        <div>トークン: {currentEmailTemplate.metadata.gptUsage.tokens.toLocaleString()}</div>
                        <div>コスト: ${currentEmailTemplate.metadata.gptUsage.cost.toFixed(3)}</div>
                      </div>
                    </div>
                  )}

                  {/* Template Info */}
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <h4 className="text-xs font-medium text-gray-700 mb-2">テンプレート情報</h4>
                    <div className="space-y-1 text-xs text-gray-600">
                      <div>バージョン: {currentEmailTemplate.metadata.templateVersion}</div>
                      <div>ユーザーID: {currentEmailTemplate.metadata.userId}</div>
                      {currentEmailTemplate.metadata.isFallbackTemplate && (
                        <Badge variant="outline" className="text-xs">
                          フォールバック使用
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Content Area */}
          <div className="flex-1 overflow-auto">
            {currentIsLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-600">メールを読み込み中...</p>
                </div>
              </div>
            ) : currentError ? (
              <div className="flex items-center justify-center h-full">
                <Card className="max-w-md">
                  <CardContent className="p-6 text-center">
                    <div className="text-red-600 mb-4">
                      <X className="h-8 w-8 mx-auto" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">エラーが発生しました</h3>
                    <p className="text-gray-600 text-sm mb-4">{currentError}</p>
                    <Button onClick={handleRegenerateEmail} size="sm">
                      再試行
                    </Button>
                  </CardContent>
                </Card>
              </div>
            ) : currentEmailTemplate ? (
              <div className="p-6">
                {renderEmailContent()}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500">
                  <Mail className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>メールテンプレートを選択してください</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailPreview;