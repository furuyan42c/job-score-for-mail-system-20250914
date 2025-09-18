/**
 * OWASP ZAP Integration Security Tests
 *
 * OWASP ZAP統合セキュリティテストスイート
 * - OWASP ZAP による自動化セキュリティスキャン
 * - OWASP Top 10 脆弱性チェック
 * - セキュリティレポート生成
 * - 高重要度の発見事項での失敗
 */

import { test, expect } from '@playwright/test';
import axios from 'axios';
import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

interface ZapAlert {
  alert: string;
  name: string;
  riskdesc: string;
  confidence: string;
  riskcode: string;
  desc: string;
  instances: Array<{
    uri: string;
    method: string;
    param: string;
    attack: string;
    evidence: string;
  }>;
}

interface ZapReport {
  site: Array<{
    '@name': string;
    '@host': string;
    '@port': string;
    alerts: ZapAlert[];
  }>;
}

class ZAPScanner {
  private zapApiKey: string;
  private zapUrl: string;
  private targetUrl: string;

  constructor() {
    this.zapApiKey = process.env.ZAP_API_KEY || 'test-api-key';
    this.zapUrl = process.env.ZAP_URL || 'http://localhost:8080';
    this.targetUrl = process.env.TARGET_URL || 'http://localhost:3000';
  }

  /**
   * Start ZAP proxy if not running
   */
  async startZAP(): Promise<void> {
    try {
      await axios.get(`${this.zapUrl}/JSON/core/view/version/`);
      console.log('ZAP is already running');
    } catch (error) {
      console.log('Starting ZAP...');

      // Start ZAP in headless mode
      const zapProcess = spawn('zap.sh', [
        '-daemon',
        '-port', '8080',
        '-config', `api.key=${this.zapApiKey}`,
        '-config', 'api.addrs.addr.name=.*',
        '-config', 'api.addrs.addr.regex=true'
      ]);

      // Wait for ZAP to start
      await this.waitForZAP();
    }
  }

  /**
   * Wait for ZAP to be ready
   */
  private async waitForZAP(maxAttempts: number = 30): Promise<void> {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        await axios.get(`${this.zapUrl}/JSON/core/view/version/?apikey=${this.zapApiKey}`);
        console.log('ZAP is ready');
        return;
      } catch (error) {
        console.log(`Waiting for ZAP... attempt ${i + 1}`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    throw new Error('ZAP failed to start');
  }

  /**
   * Create a new ZAP session
   */
  async createSession(sessionName: string): Promise<void> {
    try {
      await axios.get(`${this.zapUrl}/JSON/core/action/newSession/`, {
        params: {
          apikey: this.zapApiKey,
          name: sessionName,
          overwrite: true
        }
      });
    } catch (error) {
      console.error('Failed to create ZAP session:', error);
      throw error;
    }
  }

  /**
   * Spider scan the target application
   */
  async spiderScan(): Promise<string> {
    try {
      const response = await axios.get(`${this.zapUrl}/JSON/spider/action/scan/`, {
        params: {
          apikey: this.zapApiKey,
          url: this.targetUrl,
          maxChildren: 10,
          recurse: true
        }
      });

      const scanId = response.data.scan;
      console.log(`Spider scan started with ID: ${scanId}`);

      // Wait for spider to complete
      await this.waitForScanCompletion('spider', scanId);

      return scanId;
    } catch (error) {
      console.error('Spider scan failed:', error);
      throw error;
    }
  }

  /**
   * Perform active security scan
   */
  async activeScan(): Promise<string> {
    try {
      const response = await axios.get(`${this.zapUrl}/JSON/ascan/action/scan/`, {
        params: {
          apikey: this.zapApiKey,
          url: this.targetUrl,
          recurse: true,
          inScopeOnly: false
        }
      });

      const scanId = response.data.scan;
      console.log(`Active scan started with ID: ${scanId}`);

      // Wait for active scan to complete
      await this.waitForScanCompletion('ascan', scanId);

      return scanId;
    } catch (error) {
      console.error('Active scan failed:', error);
      throw error;
    }
  }

  /**
   * Wait for scan completion
   */
  private async waitForScanCompletion(scanType: 'spider' | 'ascan', scanId: string): Promise<void> {
    const maxWaitTime = 10 * 60 * 1000; // 10 minutes
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      try {
        const endpoint = scanType === 'spider' ? 'spider' : 'ascan';
        const response = await axios.get(`${this.zapUrl}/JSON/${endpoint}/view/status/`, {
          params: {
            apikey: this.zapApiKey,
            scanId: scanId
          }
        });

        const progress = parseInt(response.data.status);
        console.log(`${scanType} scan progress: ${progress}%`);

        if (progress >= 100) {
          console.log(`${scanType} scan completed`);
          return;
        }

        await new Promise(resolve => setTimeout(resolve, 5000));
      } catch (error) {
        console.error(`Error checking ${scanType} scan status:`, error);
        break;
      }
    }

    throw new Error(`${scanType} scan timed out`);
  }

  /**
   * Get scan alerts/results
   */
  async getAlerts(): Promise<ZapAlert[]> {
    try {
      const response = await axios.get(`${this.zapUrl}/JSON/core/view/alerts/`, {
        params: {
          apikey: this.zapApiKey,
          baseurl: this.targetUrl
        }
      });

      return response.data.alerts || [];
    } catch (error) {
      console.error('Failed to get alerts:', error);
      throw error;
    }
  }

  /**
   * Generate HTML report
   */
  async generateReport(outputPath: string): Promise<void> {
    try {
      const response = await axios.get(`${this.zapUrl}/OTHER/core/other/htmlreport/`, {
        params: {
          apikey: this.zapApiKey
        },
        responseType: 'text'
      });

      fs.writeFileSync(outputPath, response.data);
      console.log(`Report saved to: ${outputPath}`);
    } catch (error) {
      console.error('Failed to generate report:', error);
      throw error;
    }
  }

  /**
   * Stop ZAP
   */
  async stopZAP(): Promise<void> {
    try {
      await axios.get(`${this.zapUrl}/JSON/core/action/shutdown/`, {
        params: {
          apikey: this.zapApiKey
        }
      });
      console.log('ZAP stopped');
    } catch (error) {
      // ZAP might already be stopped
      console.log('ZAP stop request sent');
    }
  }
}

// Test configuration
const RISK_LEVELS = {
  HIGH: '3',
  MEDIUM: '2',
  LOW: '1',
  INFORMATIONAL: '0'
};

const OWASP_TOP_10_2021 = {
  'A01:2021 – Broken Access Control': ['Access Control'],
  'A02:2021 – Cryptographic Failures': ['Crypto', 'SSL', 'TLS'],
  'A03:2021 – Injection': ['SQL Injection', 'XSS', 'Command Injection'],
  'A04:2021 – Insecure Design': ['Design'],
  'A05:2021 – Security Misconfiguration': ['Configuration'],
  'A06:2021 – Vulnerable Components': ['Dependencies', 'Libraries'],
  'A07:2021 – Identity & Authentication Failures': ['Authentication', 'Session'],
  'A08:2021 – Software & Data Integrity Failures': ['Integrity'],
  'A09:2021 – Security Logging & Monitoring Failures': ['Logging'],
  'A10:2021 – Server-Side Request Forgery': ['SSRF']
};

test.describe('OWASP ZAP Security Scan', () => {
  let scanner: ZAPScanner;

  test.beforeAll(async () => {
    scanner = new ZAPScanner();

    // Skip if ZAP is not available
    try {
      await scanner.startZAP();
      await scanner.createSession('security-test-session');
    } catch (error) {
      console.log('ZAP not available, skipping security tests');
      test.skip();
    }
  });

  test.afterAll(async () => {
    if (scanner) {
      await scanner.stopZAP();
    }
  });

  test('Should perform comprehensive security scan', async () => {
    // Perform spider scan to discover endpoints
    console.log('Starting spider scan...');
    await scanner.spiderScan();

    // Perform active security scan
    console.log('Starting active security scan...');
    await scanner.activeScan();

    // Get scan results
    const alerts = await scanner.getAlerts();
    console.log(`Found ${alerts.length} security alerts`);

    // Generate report
    const reportPath = path.join(__dirname, '../../reports/zap-security-report.html');
    await scanner.generateReport(reportPath);

    // Analyze results
    const highRiskAlerts = alerts.filter(alert => alert.riskcode === RISK_LEVELS.HIGH);
    const mediumRiskAlerts = alerts.filter(alert => alert.riskcode === RISK_LEVELS.MEDIUM);
    const lowRiskAlerts = alerts.filter(alert => alert.riskcode === RISK_LEVELS.LOW);

    console.log(`High risk alerts: ${highRiskAlerts.length}`);
    console.log(`Medium risk alerts: ${mediumRiskAlerts.length}`);
    console.log(`Low risk alerts: ${lowRiskAlerts.length}`);

    // Log high-risk issues
    if (highRiskAlerts.length > 0) {
      console.log('HIGH RISK SECURITY ISSUES FOUND:');
      highRiskAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
        alert.instances.forEach(instance => {
          console.log(`  URL: ${instance.uri}`);
          console.log(`  Method: ${instance.method}`);
          console.log(`  Parameter: ${instance.param}`);
        });
      });
    }

    // Fail test if high-risk vulnerabilities found
    expect(highRiskAlerts.length).toBe(0,
      `Found ${highRiskAlerts.length} high-risk security vulnerabilities`);

    // Warn about medium-risk issues
    if (mediumRiskAlerts.length > 0) {
      console.warn(`WARNING: Found ${mediumRiskAlerts.length} medium-risk security issues`);
    }
  });

  test('Should check for OWASP Top 10 vulnerabilities', async () => {
    const alerts = await scanner.getAlerts();
    const owaspFindings: { [key: string]: ZapAlert[] } = {};

    // Categorize findings by OWASP Top 10
    for (const [owaspCategory, keywords] of Object.entries(OWASP_TOP_10_2021)) {
      owaspFindings[owaspCategory] = alerts.filter(alert =>
        keywords.some(keyword =>
          alert.name.toLowerCase().includes(keyword.toLowerCase()) ||
          alert.desc.toLowerCase().includes(keyword.toLowerCase())
        )
      );
    }

    // Report findings by OWASP category
    for (const [category, findings] of Object.entries(owaspFindings)) {
      if (findings.length > 0) {
        console.log(`\n${category}:`);
        findings.forEach(finding => {
          const risk = finding.riskcode === RISK_LEVELS.HIGH ? 'HIGH' :
                      finding.riskcode === RISK_LEVELS.MEDIUM ? 'MEDIUM' :
                      finding.riskcode === RISK_LEVELS.LOW ? 'LOW' : 'INFO';
          console.log(`  - [${risk}] ${finding.name}`);
        });
      }
    }

    // Check for critical OWASP Top 10 issues
    const criticalCategories = [
      'A01:2021 – Broken Access Control',
      'A02:2021 – Cryptographic Failures',
      'A03:2021 – Injection'
    ];

    for (const category of criticalCategories) {
      const highRiskFindings = owaspFindings[category]?.filter(
        alert => alert.riskcode === RISK_LEVELS.HIGH
      ) || [];

      expect(highRiskFindings.length).toBe(0,
        `Found high-risk ${category} vulnerabilities`);
    }
  });

  test('Should verify security headers', async () => {
    const alerts = await scanner.getAlerts();

    // Check for missing security headers
    const securityHeaderAlerts = alerts.filter(alert =>
      alert.name.toLowerCase().includes('header') ||
      alert.name.toLowerCase().includes('csp') ||
      alert.name.toLowerCase().includes('hsts') ||
      alert.name.toLowerCase().includes('x-frame-options')
    );

    if (securityHeaderAlerts.length > 0) {
      console.log('Security header issues found:');
      securityHeaderAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
      });
    }

    // High-risk header issues should not exist
    const highRiskHeaderAlerts = securityHeaderAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.HIGH
    );

    expect(highRiskHeaderAlerts.length).toBe(0,
      'Found high-risk security header issues');
  });

  test('Should check for sensitive information disclosure', async () => {
    const alerts = await scanner.getAlerts();

    // Look for information disclosure issues
    const infoDisclosureAlerts = alerts.filter(alert =>
      alert.name.toLowerCase().includes('disclosure') ||
      alert.name.toLowerCase().includes('information') ||
      alert.name.toLowerCase().includes('error') ||
      alert.desc.toLowerCase().includes('sensitive')
    );

    if (infoDisclosureAlerts.length > 0) {
      console.log('Information disclosure issues found:');
      infoDisclosureAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
        if (alert.instances.length > 0) {
          console.log(`  Evidence: ${alert.instances[0].evidence}`);
        }
      });
    }

    // High-risk information disclosure should not exist
    const highRiskInfoAlerts = infoDisclosureAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.HIGH
    );

    expect(highRiskInfoAlerts.length).toBe(0,
      'Found high-risk information disclosure issues');
  });

  test('Should check for injection vulnerabilities', async () => {
    const alerts = await scanner.getAlerts();

    // Check for various injection types
    const injectionTypes = [
      'SQL Injection',
      'XSS',
      'Command Injection',
      'LDAP Injection',
      'XML Injection',
      'Script Injection'
    ];

    const injectionAlerts = alerts.filter(alert =>
      injectionTypes.some(type =>
        alert.name.toLowerCase().includes(type.toLowerCase())
      )
    );

    if (injectionAlerts.length > 0) {
      console.log('Injection vulnerabilities found:');
      injectionAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
        alert.instances.forEach(instance => {
          console.log(`  Attack: ${instance.attack}`);
          console.log(`  URL: ${instance.uri}`);
        });
      });
    }

    // No high-risk injection vulnerabilities should exist
    const highRiskInjectionAlerts = injectionAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.HIGH
    );

    expect(highRiskInjectionAlerts.length).toBe(0,
      `Found ${highRiskInjectionAlerts.length} high-risk injection vulnerabilities`);

    // Medium-risk injection issues should be minimal
    const mediumRiskInjectionAlerts = injectionAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.MEDIUM
    );

    expect(mediumRiskInjectionAlerts.length).toBeLessThanOrEqual(2,
      `Found ${mediumRiskInjectionAlerts.length} medium-risk injection issues (should be <= 2)`);
  });

  test('Should verify authentication and session management', async () => {
    const alerts = await scanner.getAlerts();

    // Check for authentication/session issues
    const authAlerts = alerts.filter(alert =>
      alert.name.toLowerCase().includes('authentication') ||
      alert.name.toLowerCase().includes('session') ||
      alert.name.toLowerCase().includes('cookie') ||
      alert.name.toLowerCase().includes('login')
    );

    if (authAlerts.length > 0) {
      console.log('Authentication/Session issues found:');
      authAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
      });
    }

    // High-risk auth issues should not exist
    const highRiskAuthAlerts = authAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.HIGH
    );

    expect(highRiskAuthAlerts.length).toBe(0,
      'Found high-risk authentication/session issues');
  });

  test('Should check for access control issues', async () => {
    const alerts = await scanner.getAlerts();

    // Check for access control vulnerabilities
    const accessControlAlerts = alerts.filter(alert =>
      alert.name.toLowerCase().includes('access') ||
      alert.name.toLowerCase().includes('authorization') ||
      alert.name.toLowerCase().includes('privilege') ||
      alert.name.toLowerCase().includes('bypass')
    );

    if (accessControlAlerts.length > 0) {
      console.log('Access control issues found:');
      accessControlAlerts.forEach(alert => {
        console.log(`- ${alert.name}: ${alert.desc}`);
      });
    }

    // High-risk access control issues should not exist
    const highRiskAccessAlerts = accessControlAlerts.filter(
      alert => alert.riskcode === RISK_LEVELS.HIGH
    );

    expect(highRiskAccessAlerts.length).toBe(0,
      'Found high-risk access control issues');
  });
});

// Utility function to run ZAP scan from command line
export async function runZapScan(targetUrl: string, outputDir: string): Promise<void> {
  const scanner = new ZAPScanner();

  try {
    await scanner.startZAP();
    await scanner.createSession('cli-security-scan');

    console.log('Running spider scan...');
    await scanner.spiderScan();

    console.log('Running active scan...');
    await scanner.activeScan();

    const alerts = await scanner.getAlerts();
    console.log(`Scan completed. Found ${alerts.length} alerts.`);

    // Generate report
    const reportPath = path.join(outputDir, 'zap-security-report.html');
    await scanner.generateReport(reportPath);

    // Save alerts as JSON
    const alertsPath = path.join(outputDir, 'zap-alerts.json');
    fs.writeFileSync(alertsPath, JSON.stringify(alerts, null, 2));

    console.log(`Reports saved to ${outputDir}`);

    // Return exit code based on high-risk findings
    const highRiskCount = alerts.filter(alert => alert.riskcode === RISK_LEVELS.HIGH).length;
    if (highRiskCount > 0) {
      console.error(`Found ${highRiskCount} high-risk security issues!`);
      process.exit(1);
    }

  } finally {
    await scanner.stopZAP();
  }
}

// Run scan if called directly
if (require.main === module) {
  const targetUrl = process.argv[2] || 'http://localhost:3000';
  const outputDir = process.argv[3] || './security-reports';

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  runZapScan(targetUrl, outputDir).catch(console.error);
}