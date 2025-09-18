/**
 * Dependency Vulnerability Check Tests
 *
 * 依存関係脆弱性チェックテストスイート
 * - JavaScript パッケージの npm audit
 * - Python パッケージの safety check
 * - コンテナイメージスキャン
 * - ライセンスコンプライアンスチェック
 */

import { test, expect } from '@playwright/test';
import { execSync, spawn, ChildProcess } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';

interface NpmAuditVulnerability {
  title: string;
  severity: 'low' | 'moderate' | 'high' | 'critical';
  vulnerable_versions: string;
  patched_versions: string;
  overview: string;
  recommendation: string;
  references: string[];
  access: string;
  cwe: string[];
  cves: string[];
}

interface NpmAuditResult {
  auditReportVersion: number;
  vulnerabilities: Record<string, {
    name: string;
    severity: string;
    isDirect: boolean;
    via: Array<string | NpmAuditVulnerability>;
    effects: string[];
    range: string;
    nodes: string[];
    fixAvailable: boolean | { name: string; version: string; isSemVerMajor: boolean };
  }>;
  metadata: {
    vulnerabilities: {
      info: number;
      low: number;
      moderate: number;
      high: number;
      critical: number;
      total: number;
    };
    dependencies: {
      prod: number;
      dev: number;
      optional: number;
      peer: number;
      peerOptional: number;
      total: number;
    };
  };
}

interface YarnAuditResult {
  type: string;
  data: {
    vulnerabilities: {
      info: number;
      low: number;
      moderate: number;
      high: number;
      critical: number;
    };
    summary: string;
  };
}

interface PythonSafetyResult {
  package: string;
  installed_version: string;
  vulnerability_id: string;
  advisory: string;
  cve?: string;
  specs: string[];
}

interface LicenseInfo {
  name: string;
  version: string;
  description: string;
  repository?: string;
  license: string;
  licenseUrl?: string;
  parents: string;
}

class DependencyChecker {
  private projectRoot: string;

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
  }

  /**
   * Run npm audit for JavaScript dependencies
   */
  async runNpmAudit(): Promise<NpmAuditResult> {
    try {
      const result = execSync('npm audit --json', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return JSON.parse(result);
    } catch (error: any) {
      // npm audit returns non-zero exit code when vulnerabilities found
      if (error.stdout) {
        try {
          return JSON.parse(error.stdout);
        } catch (parseError) {
          throw new Error(`Failed to parse npm audit output: ${parseError}`);
        }
      }
      throw new Error(`npm audit failed: ${error.message}`);
    }
  }

  /**
   * Run yarn audit for JavaScript dependencies
   */
  async runYarnAudit(): Promise<YarnAuditResult[]> {
    try {
      const result = execSync('yarn audit --json', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      // Yarn audit returns multiple JSON objects
      return result.split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line))
        .filter(item => item.type === 'auditSummary');
    } catch (error: any) {
      if (error.stdout) {
        try {
          return error.stdout.split('\n')
            .filter((line: string) => line.trim())
            .map((line: string) => JSON.parse(line))
            .filter((item: any) => item.type === 'auditSummary');
        } catch (parseError) {
          throw new Error(`Failed to parse yarn audit output: ${parseError}`);
        }
      }
      throw new Error(`yarn audit failed: ${error.message}`);
    }
  }

  /**
   * Run Python safety check
   */
  async runPythonSafety(): Promise<PythonSafetyResult[]> {
    try {
      const result = execSync('safety check --json', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return JSON.parse(result);
    } catch (error: any) {
      if (error.stdout) {
        try {
          return JSON.parse(error.stdout);
        } catch (parseError) {
          // Safety might return plain text in some cases
          return this.parseSafetyTextOutput(error.stdout);
        }
      }
      throw new Error(`Python safety check failed: ${error.message}`);
    }
  }

  /**
   * Parse safety text output when JSON is not available
   */
  private parseSafetyTextOutput(output: string): PythonSafetyResult[] {
    const vulnerabilities: PythonSafetyResult[] = [];
    const lines = output.split('\n');

    for (const line of lines) {
      const match = line.match(/^(\w+)==([^\s]+).*vulnerability_id:(\w+).*advisory:(.*)$/);
      if (match) {
        vulnerabilities.push({
          package: match[1],
          installed_version: match[2],
          vulnerability_id: match[3],
          advisory: match[4].trim(),
          specs: [`>=${match[2]}`]
        });
      }
    }

    return vulnerabilities;
  }

  /**
   * Check for outdated packages
   */
  async checkOutdatedPackages(): Promise<any> {
    try {
      const result = execSync('npm outdated --json', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return JSON.parse(result || '{}');
    } catch (error: any) {
      // npm outdated returns non-zero exit code when outdated packages found
      if (error.stdout) {
        try {
          return JSON.parse(error.stdout || '{}');
        } catch (parseError) {
          return {};
        }
      }
      return {};
    }
  }

  /**
   * Check licenses of dependencies
   */
  async checkLicenses(): Promise<LicenseInfo[]> {
    try {
      // Install license-checker if not available
      try {
        execSync('npx license-checker --version', { stdio: 'pipe' });
      } catch {
        console.log('Installing license-checker...');
        execSync('npm install -g license-checker', { stdio: 'pipe' });
      }

      const result = execSync('npx license-checker --json', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      const licenseData = JSON.parse(result);
      const licenses: LicenseInfo[] = [];

      for (const [packageName, info] of Object.entries(licenseData)) {
        const [name, version] = packageName.split('@');
        licenses.push({
          name: name || packageName,
          version: version || 'unknown',
          description: (info as any).description || '',
          repository: (info as any).repository || '',
          license: (info as any).licenses || 'Unknown',
          licenseUrl: (info as any).licenseFile || '',
          parents: (info as any).parents || ''
        });
      }

      return licenses;
    } catch (error) {
      console.warn('License check failed:', error);
      return [];
    }
  }

  /**
   * Scan Docker images for vulnerabilities
   */
  async scanDockerImage(imageName: string): Promise<any> {
    try {
      // Use Trivy for container scanning
      const result = execSync(`trivy image --format json ${imageName}`, {
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return JSON.parse(result);
    } catch (error) {
      console.warn(`Docker scan failed for ${imageName}:`, error);
      return null;
    }
  }

  /**
   * Check for known malicious packages
   */
  async checkMaliciousPackages(): Promise<string[]> {
    const maliciousPackages: string[] = [];

    try {
      // Read package.json to get dependencies
      const packageJsonPath = path.join(this.projectRoot, 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
        const allDeps = {
          ...packageJson.dependencies,
          ...packageJson.devDependencies,
          ...packageJson.peerDependencies
        };

        // Known malicious package patterns (examples)
        const suspiciousPatterns = [
          /^event-stream@3\.3\.[4-6]$/,  // Known compromise
          /^eslint-scope@3\.7\.[1-2]$/,   // Known compromise
          /^.*-js$/,                      // Suspicious pattern
          /^.*jquery.*$/i,                // Typosquatting
          /^.*lodash.*$/i,                // Typosquatting
          /^.*express.*$/i                // Typosquatting
        ];

        for (const [packageName, version] of Object.entries(allDeps)) {
          const fullName = `${packageName}@${version}`;

          for (const pattern of suspiciousPatterns) {
            if (pattern.test(fullName) || pattern.test(packageName)) {
              maliciousPackages.push(fullName);
              break;
            }
          }
        }
      }
    } catch (error) {
      console.warn('Malicious package check failed:', error);
    }

    return maliciousPackages;
  }

  /**
   * Generate security report
   */
  async generateSecurityReport(outputPath: string): Promise<void> {
    const report = {
      timestamp: new Date().toISOString(),
      npm_audit: null as NpmAuditResult | null,
      python_safety: null as PythonSafetyResult[] | null,
      outdated_packages: null as any,
      licenses: null as LicenseInfo[] | null,
      malicious_packages: null as string[] | null,
      docker_scans: {} as Record<string, any>
    };

    // Run all checks
    try {
      report.npm_audit = await this.runNpmAudit();
    } catch (error) {
      console.warn('npm audit failed:', error);
    }

    try {
      report.python_safety = await this.runPythonSafety();
    } catch (error) {
      console.warn('Python safety check failed:', error);
    }

    try {
      report.outdated_packages = await this.checkOutdatedPackages();
    } catch (error) {
      console.warn('Outdated packages check failed:', error);
    }

    try {
      report.licenses = await this.checkLicenses();
    } catch (error) {
      console.warn('License check failed:', error);
    }

    try {
      report.malicious_packages = await this.checkMaliciousPackages();
    } catch (error) {
      console.warn('Malicious package check failed:', error);
    }

    // Scan common Docker images
    const dockerImages = ['node:18', 'python:3.11', 'nginx:latest'];
    for (const image of dockerImages) {
      try {
        report.docker_scans[image] = await this.scanDockerImage(image);
      } catch (error) {
        console.warn(`Docker scan failed for ${image}:`, error);
      }
    }

    // Save report
    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
    console.log(`Security report saved to: ${outputPath}`);
  }
}

// Security thresholds
const SECURITY_THRESHOLDS = {
  critical: 0,    // No critical vulnerabilities allowed
  high: 2,        // Max 2 high-severity vulnerabilities
  moderate: 10,   // Max 10 moderate vulnerabilities
  outdated_days: 365  // Max 1 year old packages
};

const FORBIDDEN_LICENSES = [
  'GPL-3.0',
  'AGPL-3.0',
  'LGPL-3.0',
  'UNLICENSED'
];

test.describe('Dependency Security Tests', () => {
  let checker: DependencyChecker;

  test.beforeAll(() => {
    checker = new DependencyChecker();
  });

  test('Should not have critical or high-severity npm vulnerabilities', async () => {
    let auditResult: NpmAuditResult;

    try {
      auditResult = await checker.runNpmAudit();
    } catch (error) {
      test.skip('npm audit not available');
      return;
    }

    const { vulnerabilities, metadata } = auditResult;
    const vulnCounts = metadata.vulnerabilities;

    console.log('NPM Audit Results:');
    console.log(`  Critical: ${vulnCounts.critical}`);
    console.log(`  High: ${vulnCounts.high}`);
    console.log(`  Moderate: ${vulnCounts.moderate}`);
    console.log(`  Low: ${vulnCounts.low}`);
    console.log(`  Total: ${vulnCounts.total}`);

    // List critical and high vulnerabilities
    if (vulnCounts.critical > 0 || vulnCounts.high > 0) {
      console.log('\nHigh-priority vulnerabilities found:');

      for (const [name, vuln] of Object.entries(vulnerabilities)) {
        if (vuln.severity === 'critical' || vuln.severity === 'high') {
          console.log(`  - ${name} (${vuln.severity}): ${vuln.range}`);

          if (Array.isArray(vuln.via)) {
            vuln.via.forEach(via => {
              if (typeof via === 'object') {
                console.log(`    ${via.title}: ${via.overview}`);
                console.log(`    Fix: ${via.recommendation}`);
              }
            });
          }
        }
      }
    }

    // Enforce security thresholds
    expect(vulnCounts.critical).toBeLessThanOrEqual(SECURITY_THRESHOLDS.critical);
    expect(vulnCounts.high).toBeLessThanOrEqual(SECURITY_THRESHOLDS.high);
    expect(vulnCounts.moderate).toBeLessThanOrEqual(SECURITY_THRESHOLDS.moderate);
  });

  test('Should not have Python package vulnerabilities', async () => {
    let safetyResults: PythonSafetyResult[];

    try {
      safetyResults = await checker.runPythonSafety();
    } catch (error) {
      test.skip('Python safety check not available');
      return;
    }

    console.log(`Python Safety Results: ${safetyResults.length} vulnerabilities found`);

    if (safetyResults.length > 0) {
      console.log('Python vulnerabilities found:');
      safetyResults.forEach(vuln => {
        console.log(`  - ${vuln.package} ${vuln.installed_version}`);
        console.log(`    Vulnerability: ${vuln.vulnerability_id}`);
        console.log(`    Advisory: ${vuln.advisory}`);
        if (vuln.cve) {
          console.log(`    CVE: ${vuln.cve}`);
        }
      });
    }

    // Should have no critical Python vulnerabilities
    expect(safetyResults.length).toBe(0,
      `Found ${safetyResults.length} Python package vulnerabilities`);
  });

  test('Should not have severely outdated packages', async () => {
    const outdatedPackages = await checker.checkOutdatedPackages();
    const severelyOutdated: string[] = [];

    for (const [packageName, info] of Object.entries(outdatedPackages)) {
      const packageInfo = info as any;

      // Check if package is more than 1 year behind latest
      if (packageInfo.current && packageInfo.latest) {
        // This is a simplified check - in reality you'd compare dates
        const currentVersion = packageInfo.current.split('.').map(Number);
        const latestVersion = packageInfo.latest.split('.').map(Number);

        // Consider severely outdated if major version is 2+ behind
        if (latestVersion[0] - currentVersion[0] >= 2) {
          severelyOutdated.push(`${packageName}: ${packageInfo.current} -> ${packageInfo.latest}`);
        }
      }
    }

    if (severelyOutdated.length > 0) {
      console.log('Severely outdated packages:');
      severelyOutdated.forEach(pkg => console.log(`  - ${pkg}`));
    }

    expect(severelyOutdated.length).toBeLessThanOrEqual(5,
      `Found ${severelyOutdated.length} severely outdated packages`);
  });

  test('Should not have forbidden licenses', async () => {
    const licenses = await checker.checkLicenses();
    const forbiddenLicensePackages: string[] = [];

    for (const licenseInfo of licenses) {
      if (FORBIDDEN_LICENSES.some(forbidden =>
        licenseInfo.license.toLowerCase().includes(forbidden.toLowerCase())
      )) {
        forbiddenLicensePackages.push(
          `${licenseInfo.name}@${licenseInfo.version}: ${licenseInfo.license}`
        );
      }
    }

    if (forbiddenLicensePackages.length > 0) {
      console.log('Packages with forbidden licenses:');
      forbiddenLicensePackages.forEach(pkg => console.log(`  - ${pkg}`));
    }

    expect(forbiddenLicensePackages.length).toBe(0,
      `Found packages with forbidden licenses: ${forbiddenLicensePackages.join(', ')}`);
  });

  test('Should not have unknown or missing licenses', async () => {
    const licenses = await checker.checkLicenses();
    const unknownLicensePackages: string[] = [];

    for (const licenseInfo of licenses) {
      const license = licenseInfo.license.toLowerCase();

      if (license.includes('unknown') ||
          license.includes('unlicensed') ||
          license === '' ||
          license === 'n/a') {
        unknownLicensePackages.push(
          `${licenseInfo.name}@${licenseInfo.version}: ${licenseInfo.license}`
        );
      }
    }

    if (unknownLicensePackages.length > 0) {
      console.log('Packages with unknown licenses:');
      unknownLicensePackages.forEach(pkg => console.log(`  - ${pkg}`));
    }

    // Allow some packages with unknown licenses but limit the count
    expect(unknownLicensePackages.length).toBeLessThanOrEqual(10,
      `Too many packages with unknown licenses: ${unknownLicensePackages.length}`);
  });

  test('Should not have known malicious packages', async () => {
    const maliciousPackages = await checker.checkMaliciousPackages();

    if (maliciousPackages.length > 0) {
      console.log('Potentially malicious packages found:');
      maliciousPackages.forEach(pkg => console.log(`  - ${pkg}`));
    }

    expect(maliciousPackages.length).toBe(0,
      `Found potentially malicious packages: ${maliciousPackages.join(', ')}`);
  });

  test('Should generate comprehensive security report', async () => {
    const reportPath = path.join(__dirname, '../../reports/dependency-security-report.json');

    // Ensure reports directory exists
    const reportsDir = path.dirname(reportPath);
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    await checker.generateSecurityReport(reportPath);

    // Verify report was created
    expect(fs.existsSync(reportPath)).toBe(true);

    // Validate report structure
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));

    expect(report).toHaveProperty('timestamp');
    expect(report).toHaveProperty('npm_audit');
    expect(report).toHaveProperty('licenses');
    expect(report).toHaveProperty('malicious_packages');

    console.log(`Security report generated: ${reportPath}`);
  });

  test('Should validate package integrity', async () => {
    // Check package-lock.json exists and is up to date
    const packageLockPath = path.join(process.cwd(), 'package-lock.json');
    const packageJsonPath = path.join(process.cwd(), 'package.json');

    if (fs.existsSync(packageJsonPath) && fs.existsSync(packageLockPath)) {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
      const packageLock = JSON.parse(fs.readFileSync(packageLockPath, 'utf-8'));

      // Verify lockfile version matches package.json
      expect(packageLock.name).toBe(packageJson.name);
      expect(packageLock.version).toBe(packageJson.version);

      // Check for integrity hashes
      if (packageLock.packages) {
        let packagesWithIntegrity = 0;
        let totalPackages = 0;

        for (const [name, pkg] of Object.entries(packageLock.packages)) {
          if (name !== '') { // Skip root package
            totalPackages++;
            if ((pkg as any).integrity) {
              packagesWithIntegrity++;
            }
          }
        }

        console.log(`Package integrity: ${packagesWithIntegrity}/${totalPackages} packages have integrity hashes`);

        // Most packages should have integrity hashes
        const integrityRatio = packagesWithIntegrity / totalPackages;
        expect(integrityRatio).toBeGreaterThan(0.8);
      }
    } else {
      console.log('package-lock.json not found - skipping integrity check');
    }
  });
});

// CLI interface for running security checks
export async function runSecurityChecks(): Promise<void> {
  const checker = new DependencyChecker();
  const reportPath = './security-reports/dependency-report.json';

  console.log('Running comprehensive dependency security checks...');

  try {
    await checker.generateSecurityReport(reportPath);
    console.log('✅ Security checks completed successfully');

    // Check if any critical issues were found
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));

    let hasHightRiskIssues = false;

    if (report.npm_audit?.metadata?.vulnerabilities?.critical > 0) {
      console.error('❌ Critical npm vulnerabilities found');
      hasHightRiskIssues = true;
    }

    if (report.python_safety && report.python_safety.length > 0) {
      console.error('❌ Python package vulnerabilities found');
      hasHightRiskIssues = true;
    }

    if (report.malicious_packages && report.malicious_packages.length > 0) {
      console.error('❌ Potentially malicious packages found');
      hasHightRiskIssues = true;
    }

    if (hasHightRiskIssues) {
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Security checks failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  runSecurityChecks();
}