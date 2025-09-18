import { Page, Locator } from '@playwright/test';

/**
 * Base Page Object Model class that provides common functionality for all pages
 */
export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a specific URL
   */
  async goto(url: string): Promise<void> {
    await this.page.goto(url);
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(name: string): Promise<Buffer> {
    return await this.page.screenshot({ fullPage: true, path: `test-results/${name}.png` });
  }

  /**
   * Get element by test ID
   */
  getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  /**
   * Get element by role and name
   */
  getByRoleAndName(role: 'button' | 'link' | 'textbox' | 'heading' | 'tab' | 'listitem', name: string): Locator {
    return this.page.getByRole(role, { name });
  }

  /**
   * Wait for element to be visible
   */
  async waitForVisible(locator: Locator): Promise<void> {
    await locator.waitFor({ state: 'visible' });
  }

  /**
   * Fill input field with value
   */
  async fillInput(locator: Locator, value: string): Promise<void> {
    await locator.fill(value);
  }

  /**
   * Click element with wait
   */
  async clickElement(locator: Locator): Promise<void> {
    await locator.waitFor({ state: 'visible' });
    await locator.click();
  }

  /**
   * Verify element text content
   */
  async verifyText(locator: Locator, expectedText: string): Promise<void> {
    await this.page.waitForFunction(
      ([element, text]) => element?.textContent?.includes(text),
      [await locator.elementHandle(), expectedText],
      { timeout: 10000 }
    );
  }

  /**
   * Check if element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    return await locator.isVisible();
  }

  /**
   * Get current URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * Wait for URL to change
   */
  async waitForUrlChange(expectedPath: string): Promise<void> {
    await this.page.waitForURL(`**${expectedPath}**`);
  }

  /**
   * Handle alert dialogs
   */
  async handleAlert(accept: boolean = true): Promise<void> {
    this.page.on('dialog', async dialog => {
      if (accept) {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }

  /**
   * Wait for API response
   */
  async waitForApiResponse(url: string | RegExp, timeout: number = 30000): Promise<void> {
    await this.page.waitForResponse(url, { timeout });
  }

  /**
   * Monitor console errors
   */
  async monitorConsoleErrors(): Promise<string[]> {
    const errors: string[] = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    return errors;
  }

  /**
   * Check for network failures
   */
  async monitorNetworkFailures(): Promise<string[]> {
    const failures: string[] = [];
    this.page.on('response', response => {
      if (!response.ok()) {
        failures.push(`${response.status()} - ${response.url()}`);
      }
    });
    return failures;
  }

  /**
   * Simulate keyboard shortcut
   */
  async pressKeyboard(keys: string): Promise<void> {
    await this.page.keyboard.press(keys);
  }

  /**
   * Scroll to element
   */
  async scrollToElement(locator: Locator): Promise<void> {
    await locator.scrollIntoViewIfNeeded();
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingToComplete(): Promise<void> {
    // Wait for any loading spinners to disappear
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('[data-testid*="loading"], .loading, .spinner');
      return loadingElements.length === 0 || Array.from(loadingElements).every(el =>
        window.getComputedStyle(el as HTMLElement).display === 'none'
      );
    }, { timeout: 30000 });
  }
}