import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Authentication Page Object Model (Login/Registration)
 */
export class AuthPage extends BasePage {
  // Common elements
  readonly authContainer: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;
  readonly toggleFormLink: Locator;

  // Registration specific
  readonly confirmPasswordInput: Locator;
  readonly firstNameInput: Locator;
  readonly lastNameInput: Locator;
  readonly termsCheckbox: Locator;

  // Login specific
  readonly forgotPasswordLink: Locator;
  readonly rememberMeCheckbox: Locator;

  constructor(page: Page) {
    super(page);

    // Common elements
    this.authContainer = this.getByTestId('auth-container');
    this.emailInput = this.getByTestId('email-input');
    this.passwordInput = this.getByTestId('password-input');
    this.submitButton = this.getByTestId('submit-button');
    this.errorMessage = this.getByTestId('error-message');
    this.successMessage = this.getByTestId('success-message');
    this.toggleFormLink = this.getByTestId('toggle-form-link');

    // Registration specific
    this.confirmPasswordInput = this.getByTestId('confirm-password-input');
    this.firstNameInput = this.getByTestId('first-name-input');
    this.lastNameInput = this.getByTestId('last-name-input');
    this.termsCheckbox = this.getByTestId('terms-checkbox');

    // Login specific
    this.forgotPasswordLink = this.getByTestId('forgot-password-link');
    this.rememberMeCheckbox = this.getByTestId('remember-me-checkbox');
  }

  /**
   * Navigate to login page
   */
  async gotoLogin(): Promise<void> {
    await super.goto('/login');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to registration page
   */
  async gotoRegister(): Promise<void> {
    await super.goto('/register');
    await this.waitForPageLoad();
  }

  /**
   * Fill login form
   */
  async fillLoginForm(email: string, password: string, rememberMe: boolean = false): Promise<void> {
    await this.fillInput(this.emailInput, email);
    await this.fillInput(this.passwordInput, password);

    if (rememberMe) {
      await this.clickElement(this.rememberMeCheckbox);
    }
  }

  /**
   * Fill registration form
   */
  async fillRegistrationForm(
    firstName: string,
    lastName: string,
    email: string,
    password: string,
    confirmPassword: string,
    acceptTerms: boolean = true
  ): Promise<void> {
    await this.fillInput(this.firstNameInput, firstName);
    await this.fillInput(this.lastNameInput, lastName);
    await this.fillInput(this.emailInput, email);
    await this.fillInput(this.passwordInput, password);
    await this.fillInput(this.confirmPasswordInput, confirmPassword);

    if (acceptTerms) {
      await this.clickElement(this.termsCheckbox);
    }
  }

  /**
   * Submit authentication form
   */
  async submitForm(): Promise<void> {
    await this.clickElement(this.submitButton);
  }

  /**
   * Perform complete login
   */
  async login(email: string, password: string, rememberMe: boolean = false): Promise<void> {
    await this.fillLoginForm(email, password, rememberMe);
    await this.submitForm();
  }

  /**
   * Perform complete registration
   */
  async register(
    firstName: string,
    lastName: string,
    email: string,
    password: string,
    confirmPassword: string = '',
    acceptTerms: boolean = true
  ): Promise<void> {
    const confirmPwd = confirmPassword || password;
    await this.fillRegistrationForm(firstName, lastName, email, password, confirmPwd, acceptTerms);
    await this.submitForm();
  }

  /**
   * Toggle between login and registration forms
   */
  async toggleForm(): Promise<void> {
    await this.clickElement(this.toggleFormLink);
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword(): Promise<void> {
    await this.clickElement(this.forgotPasswordLink);
  }

  /**
   * Verify authentication page is loaded
   */
  async verifyAuthPageLoaded(): Promise<void> {
    await this.waitForVisible(this.authContainer);
    await this.waitForVisible(this.emailInput);
    await this.waitForVisible(this.passwordInput);
    await this.waitForVisible(this.submitButton);
  }

  /**
   * Verify login form is displayed
   */
  async verifyLoginForm(): Promise<void> {
    await this.verifyAuthPageLoaded();
    await this.waitForVisible(this.forgotPasswordLink);
    await this.waitForVisible(this.rememberMeCheckbox);
  }

  /**
   * Verify registration form is displayed
   */
  async verifyRegistrationForm(): Promise<void> {
    await this.verifyAuthPageLoaded();
    await this.waitForVisible(this.firstNameInput);
    await this.waitForVisible(this.lastNameInput);
    await this.waitForVisible(this.confirmPasswordInput);
    await this.waitForVisible(this.termsCheckbox);
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    await this.waitForVisible(this.errorMessage);
    return await this.errorMessage.textContent() || '';
  }

  /**
   * Get success message text
   */
  async getSuccessMessage(): Promise<string> {
    await this.waitForVisible(this.successMessage);
    return await this.successMessage.textContent() || '';
  }

  /**
   * Verify successful authentication (redirected to dashboard/profile)
   */
  async verifyAuthenticationSuccess(): Promise<void> {
    // Wait for redirect to dashboard or profile page
    await this.page.waitForURL(/\/(dashboard|profile)/, { timeout: 10000 });
  }

  /**
   * Verify authentication failure (error message displayed)
   */
  async verifyAuthenticationError(expectedError?: string): Promise<void> {
    await this.waitForVisible(this.errorMessage);
    if (expectedError) {
      await this.verifyText(this.errorMessage, expectedError);
    }
  }

  /**
   * Check if form validation errors are displayed
   */
  async hasValidationErrors(): Promise<boolean> {
    const validationErrors = this.page.locator('[data-testid*="validation-error"]');
    return await validationErrors.first().isVisible();
  }

  /**
   * Get validation error messages
   */
  async getValidationErrors(): Promise<string[]> {
    const validationErrors = this.page.locator('[data-testid*="validation-error"]');
    const count = await validationErrors.count();
    const errors: string[] = [];

    for (let i = 0; i < count; i++) {
      const errorText = await validationErrors.nth(i).textContent();
      if (errorText) {
        errors.push(errorText);
      }
    }

    return errors;
  }
}