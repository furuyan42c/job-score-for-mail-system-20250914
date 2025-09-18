import { EmailTemplate, Job, EmailSection, User } from './types';

// Mock data generators for testing and development
export const generateMockJob = (overrides: Partial<Job> = {}): Job => ({
  id: Math.floor(Math.random() * 1000000),
  title: 'フロントエンドエンジニア（React/TypeScript）',
  companyName: '株式会社テックカンパニー',
  location: '東京都渋谷区',
  salaryMin: 3000,
  salaryMax: 5000,
  salaryType: 'monthly',
  matchScore: Math.floor(Math.random() * 40) + 60, // 60-100%
  tags: ['リモートOK', '未経験歓迎', '土日祝休み'],
  applyUrl: 'https://example.com/apply',
  isNew: Math.random() > 0.7,
  isPopular: Math.random() > 0.8,
  occupationCategory: 'エンジニア',
  employmentType: '正社員',
  ...overrides
});

export const generateMockJobs = (count: number, overrides: Partial<Job> = {}): Job[] => {
  return Array.from({ length: count }, (_, index) =>
    generateMockJob({ ...overrides, id: index + 1 })
  );
};

export const generateMockEmailSections = (): EmailSection[] => [
  {
    id: 'editorial-picks',
    title: '🏆 編集部おすすめ',
    description: '編集部が厳選したあなたにぴったりの求人をお届けします。',
    jobs: generateMockJobs(5, {
      matchScore: Math.floor(Math.random() * 10) + 85,
      isPopular: true
    }),
    maxJobs: 5,
    priority: 1
  },
  {
    id: 'top-recommendations',
    title: '🎯 TOP5 おすすめ',
    description: 'あなたのプロフィールに基づいて最もマッチ度の高い求人です。',
    jobs: generateMockJobs(5, {
      matchScore: Math.floor(Math.random() * 15) + 80
    }),
    maxJobs: 5,
    priority: 2
  },
  {
    id: 'personalized-picks',
    title: '💝 あなた専用求人',
    description: 'あなたの経験やスキルを活かせる求人を10件ピックアップしました。',
    jobs: generateMockJobs(10, {
      matchScore: Math.floor(Math.random() * 20) + 70
    }),
    maxJobs: 10,
    priority: 3
  },
  {
    id: 'new-arrivals',
    title: '🆕 新着求人',
    description: '昨日新しく追加された求人から、あなたにマッチするものをご紹介。',
    jobs: generateMockJobs(10, {
      isNew: true,
      matchScore: Math.floor(Math.random() * 30) + 60
    }),
    maxJobs: 10,
    priority: 4
  },
  {
    id: 'popular-jobs',
    title: '🔥 人気の求人',
    description: '多くの人が注目している人気の求人をチェックしてみませんか？',
    jobs: generateMockJobs(5, {
      isPopular: true,
      matchScore: Math.floor(Math.random() * 25) + 65
    }),
    maxJobs: 5,
    priority: 5
  },
  {
    id: 'you-might-like',
    title: '😊 こちらもおすすめ',
    description: '似たような求人を探している人が応募している求人です。',
    jobs: generateMockJobs(5, {
      matchScore: Math.floor(Math.random() * 35) + 55
    }),
    maxJobs: 5,
    priority: 6
  }
];

export const generateMockEmailTemplate = (userId?: string): EmailTemplate => {
  const sections = generateMockEmailSections();
  const totalJobs = sections.reduce((sum, section) => sum + section.jobs.length, 0);

  return {
    id: `email_${Date.now()}`,
    name: 'デイリー求人メール',
    subject: '📧 ゲットバイト通信　${date}号 - ${totalJobs}件の新着求人',
    fromAddress: 'noreply@getbaito.com',
    sections,
    metadata: {
      generatedAt: new Date().toISOString(),
      userId: userId || 'user_123',
      userName: '田中太郎',
      userLocation: '東京都渋谷区',
      totalJobCount: totalJobs,
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
};

export const generateMockUsers = (): User[] => [
  {
    id: 'user_123',
    name: '田中太郎',
    email: 'tanaka@example.com',
    location: '東京都渋谷区',
    preferences: {
      occupations: ['エンジニア', 'デザイナー'],
      locations: ['東京都', '神奈川県'],
      salaryRange: { min: 3000, max: 6000 },
      employmentTypes: ['正社員', '契約社員']
    }
  },
  {
    id: 'user_456',
    name: '佐藤花子',
    email: 'sato@example.com',
    location: '大阪府大阪市',
    preferences: {
      occupations: ['営業', 'マーケティング'],
      locations: ['大阪府', '京都府'],
      salaryRange: { min: 2500, max: 4500 },
      employmentTypes: ['正社員', 'アルバイト']
    }
  },
  {
    id: 'user_789',
    name: '山田次郎',
    email: 'yamada@example.com',
    location: '福岡県福岡市',
    preferences: {
      occupations: ['販売', '接客'],
      locations: ['福岡県'],
      salaryRange: { min: 900, max: 1500 },
      employmentTypes: ['アルバイト', 'パート']
    }
  }
];

// Utility functions for email content
export const formatSubjectLine = (template: string, variables: Record<string, any>): string => {
  return template.replace(/\$\{(\w+)\}/g, (match, key) => {
    return variables[key] ?? match;
  });
};

export const generateEmailSubjectVariables = (emailTemplate: EmailTemplate) => {
  const today = new Date();
  const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;

  return {
    date: dateStr,
    totalJobs: emailTemplate.metadata.totalJobCount,
    userName: emailTemplate.metadata.userName,
    location: emailTemplate.metadata.userLocation
  };
};

export const convertToPlainText = (emailTemplate: EmailTemplate): string => {
  const variables = generateEmailSubjectVariables(emailTemplate);
  const subject = formatSubjectLine(emailTemplate.subject, variables);

  let plainText = `件名: ${subject}\n`;
  plainText += `送信者: ${emailTemplate.fromAddress}\n`;
  plainText += `配信日: ${emailTemplate.metadata.deliveryDate}\n`;
  plainText += `\n`;

  plainText += `${emailTemplate.metadata.userName}さん、こんにちは！\n`;
  plainText += `${emailTemplate.metadata.userLocation}の求人情報をお届けします。\n\n`;

  emailTemplate.sections.forEach(section => {
    plainText += `■ ${section.title}\n`;
    if (section.description) {
      plainText += `${section.description}\n`;
    }
    plainText += `\n`;

    section.jobs.forEach((job, index) => {
      plainText += `${index + 1}. ${job.title}\n`;
      plainText += `   会社: ${job.companyName}\n`;
      plainText += `   場所: ${job.location}\n`;
      if (job.salaryMin && job.salaryMax) {
        const salaryType = job.salaryType === 'hourly' ? '時給' :
                          job.salaryType === 'monthly' ? '月給' : '年収';
        plainText += `   ${salaryType}: ¥${job.salaryMin.toLocaleString()} - ¥${job.salaryMax.toLocaleString()}\n`;
      }
      plainText += `   マッチ度: ${job.matchScore}%\n`;
      plainText += `   応募URL: ${job.applyUrl}\n\n`;
    });

    plainText += `\n`;
  });

  plainText += `---\n`;
  plainText += `このメールは${emailTemplate.metadata.gptUsage?.model || 'AI'}により生成されました。\n`;
  plainText += `生成日時: ${new Date(emailTemplate.metadata.generatedAt).toLocaleString('ja-JP')}\n`;

  return plainText;
};

export const convertToHTMLSource = (emailTemplate: EmailTemplate): string => {
  const variables = generateEmailSubjectVariables(emailTemplate);
  const subject = formatSubjectLine(emailTemplate.subject, variables);

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${subject}</title>
  <style>
    body { font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .section { margin-bottom: 30px; }
    .section-title { color: #2563eb; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .job-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .job-title { font-weight: bold; color: #1f2937; margin-bottom: 8px; }
    .job-company { color: #6b7280; margin-bottom: 8px; }
    .job-details { font-size: 14px; color: #4b5563; }
    .match-score { background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    .apply-button { background: #2563eb; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; display: inline-block; margin-top: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📧 ゲットバイト通信</h1>
      <p>${emailTemplate.metadata.userName}さん、${emailTemplate.metadata.userLocation}の求人情報をお届けします</p>
    </div>

    ${emailTemplate.sections.map(section => `
    <div class="section">
      <h2 class="section-title">${section.title}</h2>
      ${section.description ? `<p>${section.description}</p>` : ''}

      ${section.jobs.map(job => `
      <div class="job-card">
        <div class="job-title">${job.title}</div>
        <div class="job-company">${job.companyName}</div>
        <div class="job-details">
          📍 ${job.location}
          ${job.salaryMin && job.salaryMax ? `| 💰 ¥${job.salaryMin.toLocaleString()} - ¥${job.salaryMax.toLocaleString()}` : ''}
          | <span class="match-score">マッチ度 ${job.matchScore}%</span>
        </div>
        <a href="${job.applyUrl}" class="apply-button">応募する</a>
      </div>
      `).join('')}
    </div>
    `).join('')}

    <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; font-size: 12px; color: #6b7280;">
      <p>このメールは${emailTemplate.metadata.gptUsage?.model || 'AI'}により生成されました。</p>
      <p>生成日時: ${new Date(emailTemplate.metadata.generatedAt).toLocaleString('ja-JP')}</p>
    </div>
  </div>
</body>
</html>`;
};