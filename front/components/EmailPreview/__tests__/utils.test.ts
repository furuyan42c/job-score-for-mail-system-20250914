import {
  generateMockJob,
  generateMockJobs,
  generateMockEmailSections,
  generateMockEmailTemplate,
  generateMockUsers,
  formatSubjectLine,
  generateEmailSubjectVariables,
  convertToPlainText,
  convertToHTMLSource
} from '../utils';

describe('EmailPreview Utils', () => {
  describe('generateMockJob', () => {
    it('generates a job with default values', () => {
      const job = generateMockJob();

      expect(job).toHaveProperty('id');
      expect(job).toHaveProperty('title');
      expect(job).toHaveProperty('companyName');
      expect(job).toHaveProperty('location');
      expect(job).toHaveProperty('matchScore');
      expect(job).toHaveProperty('applyUrl');
      expect(typeof job.id).toBe('number');
      expect(typeof job.title).toBe('string');
      expect(typeof job.companyName).toBe('string');
      expect(typeof job.matchScore).toBe('number');
      expect(job.matchScore).toBeGreaterThanOrEqual(60);
      expect(job.matchScore).toBeLessThanOrEqual(100);
    });

    it('applies overrides correctly', () => {
      const overrides = {
        id: 123,
        title: 'Custom Title',
        matchScore: 95
      };

      const job = generateMockJob(overrides);

      expect(job.id).toBe(123);
      expect(job.title).toBe('Custom Title');
      expect(job.matchScore).toBe(95);
    });
  });

  describe('generateMockJobs', () => {
    it('generates the correct number of jobs', () => {
      const jobs = generateMockJobs(5);

      expect(jobs).toHaveLength(5);
      expect(jobs[0].id).toBe(1);
      expect(jobs[4].id).toBe(5);
    });

    it('applies overrides to all jobs', () => {
      const overrides = { matchScore: 90 };
      const jobs = generateMockJobs(3, overrides);

      jobs.forEach(job => {
        expect(job.matchScore).toBe(90);
      });
    });
  });

  describe('generateMockEmailSections', () => {
    it('generates all required sections', () => {
      const sections = generateMockEmailSections();

      expect(sections).toHaveLength(6);

      const sectionIds = sections.map(section => section.id);
      expect(sectionIds).toContain('editorial-picks');
      expect(sectionIds).toContain('top-recommendations');
      expect(sectionIds).toContain('personalized-picks');
      expect(sectionIds).toContain('new-arrivals');
      expect(sectionIds).toContain('popular-jobs');
      expect(sectionIds).toContain('you-might-like');
    });

    it('generates sections with correct job counts', () => {
      const sections = generateMockEmailSections();

      const editorialPicks = sections.find(s => s.id === 'editorial-picks');
      const personalizedPicks = sections.find(s => s.id === 'personalized-picks');

      expect(editorialPicks?.jobs).toHaveLength(5);
      expect(personalizedPicks?.jobs).toHaveLength(10);
    });

    it('generates sections with appropriate priorities', () => {
      const sections = generateMockEmailSections();

      sections.forEach(section => {
        expect(section.priority).toBeGreaterThan(0);
        expect(section.priority).toBeLessThanOrEqual(6);
      });

      // Editorial picks should have priority 1
      const editorialPicks = sections.find(s => s.id === 'editorial-picks');
      expect(editorialPicks?.priority).toBe(1);
    });
  });

  describe('generateMockEmailTemplate', () => {
    it('generates a complete email template', () => {
      const template = generateMockEmailTemplate();

      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('subject');
      expect(template).toHaveProperty('fromAddress');
      expect(template).toHaveProperty('sections');
      expect(template).toHaveProperty('metadata');

      expect(template.sections).toHaveLength(6);
      expect(template.metadata).toHaveProperty('generatedAt');
      expect(template.metadata).toHaveProperty('userId');
      expect(template.metadata).toHaveProperty('totalJobCount');
    });

    it('calculates total job count correctly', () => {
      const template = generateMockEmailTemplate();

      const calculatedTotal = template.sections.reduce(
        (sum, section) => sum + section.jobs.length,
        0
      );

      expect(template.metadata.totalJobCount).toBe(calculatedTotal);
    });

    it('uses provided userId', () => {
      const userId = 'custom-user-123';
      const template = generateMockEmailTemplate(userId);

      expect(template.metadata.userId).toBe(userId);
    });
  });

  describe('generateMockUsers', () => {
    it('generates the correct number of users', () => {
      const users = generateMockUsers();

      expect(users).toHaveLength(3);
    });

    it('generates users with required properties', () => {
      const users = generateMockUsers();

      users.forEach(user => {
        expect(user).toHaveProperty('id');
        expect(user).toHaveProperty('name');
        expect(user).toHaveProperty('email');
        expect(user).toHaveProperty('location');
        expect(user).toHaveProperty('preferences');

        expect(user.preferences).toHaveProperty('occupations');
        expect(user.preferences).toHaveProperty('locations');
        expect(user.preferences).toHaveProperty('salaryRange');
        expect(user.preferences).toHaveProperty('employmentTypes');
      });
    });
  });

  describe('formatSubjectLine', () => {
    it('replaces variables in template', () => {
      const template = '📧 ゲットバイト通信　${date}号 - ${totalJobs}件の新着求人';
      const variables = {
        date: '2024年1月15日',
        totalJobs: 42
      };

      const result = formatSubjectLine(template, variables);

      expect(result).toBe('📧 ゲットバイト通信　2024年1月15日号 - 42件の新着求人');
    });

    it('leaves unmatched variables unchanged', () => {
      const template = 'Hello ${name}, today is ${date}';
      const variables = { name: 'John' };

      const result = formatSubjectLine(template, variables);

      expect(result).toBe('Hello John, today is ${date}');
    });

    it('handles empty variables object', () => {
      const template = 'Hello ${name}';
      const variables = {};

      const result = formatSubjectLine(template, variables);

      expect(result).toBe('Hello ${name}');
    });
  });

  describe('generateEmailSubjectVariables', () => {
    it('generates variables from email template', () => {
      const template = generateMockEmailTemplate();
      const variables = generateEmailSubjectVariables(template);

      expect(variables).toHaveProperty('date');
      expect(variables).toHaveProperty('totalJobs');
      expect(variables).toHaveProperty('userName');
      expect(variables).toHaveProperty('location');

      expect(variables.totalJobs).toBe(template.metadata.totalJobCount);
      expect(variables.userName).toBe(template.metadata.userName);
      expect(variables.location).toBe(template.metadata.userLocation);
    });

    it('generates correct date format', () => {
      const template = generateMockEmailTemplate();
      const variables = generateEmailSubjectVariables(template);

      expect(variables.date).toMatch(/\d{4}年\d{1,2}月\d{1,2}日/);
    });
  });

  describe('convertToPlainText', () => {
    it('converts email template to plain text', () => {
      const template = generateMockEmailTemplate();
      const plainText = convertToPlainText(template);

      expect(plainText).toContain('件名:');
      expect(plainText).toContain('送信者:');
      expect(plainText).toContain('配信日:');
      expect(plainText).toContain(template.metadata.userName);
      expect(plainText).toContain(template.metadata.userLocation);

      // Should contain section titles
      template.sections.forEach(section => {
        expect(plainText).toContain(section.title);
      });

      // Should contain job information
      template.sections.forEach(section => {
        section.jobs.forEach(job => {
          expect(plainText).toContain(job.title);
          expect(plainText).toContain(job.companyName);
        });
      });
    });

    it('includes AI generation information', () => {
      const template = generateMockEmailTemplate();
      const plainText = convertToPlainText(template);

      expect(plainText).toContain('このメールは');
      expect(plainText).toContain('により生成されました');
      expect(plainText).toContain('生成日時:');
    });
  });

  describe('convertToHTMLSource', () => {
    it('converts email template to HTML', () => {
      const template = generateMockEmailTemplate();
      const html = convertToHTMLSource(template);

      expect(html).toContain('<!DOCTYPE html>');
      expect(html).toContain('<html lang="ja">');
      expect(html).toContain('</html>');
      expect(html).toContain('<title>');
      expect(html).toContain('</title>');

      // Should contain user information
      expect(html).toContain(template.metadata.userName);
      expect(html).toContain(template.metadata.userLocation);

      // Should contain section content
      template.sections.forEach(section => {
        expect(html).toContain(section.title);
        section.jobs.forEach(job => {
          expect(html).toContain(job.title);
          expect(html).toContain(job.companyName);
        });
      });
    });

    it('includes CSS styles', () => {
      const template = generateMockEmailTemplate();
      const html = convertToHTMLSource(template);

      expect(html).toContain('<style>');
      expect(html).toContain('font-family:');
      expect(html).toContain('.container');
      expect(html).toContain('.job-card');
    });

    it('includes AI generation footer', () => {
      const template = generateMockEmailTemplate();
      const html = convertToHTMLSource(template);

      expect(html).toContain('このメールは');
      expect(html).toContain('により生成されました');
    });
  });
});