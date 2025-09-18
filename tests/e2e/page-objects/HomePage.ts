import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Home Page Object Model
 */
export class HomePage extends BasePage {
  // Locators
  readonly heroSection: Locator;
  readonly signUpButton: Locator;
  readonly loginButton: Locator;
  readonly searchJobsButton: Locator;
  readonly featuredJobs: Locator;
  readonly navigationMenu: Locator;
  readonly logoLink: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize locators
    this.heroSection = this.getByTestId('hero-section');
    this.signUpButton = this.getByRoleAndName('button', 'Sign Up');
    this.loginButton = this.getByRoleAndName('button', 'Log In');
    this.searchJobsButton = this.getByRoleAndName('button', 'Search Jobs');
    this.featuredJobs = this.getByTestId('featured-jobs');
    this.navigationMenu = this.getByTestId('navigation-menu');
    this.logoLink = this.getByTestId('logo-link');
  }

  /**
   * Navigate to home page
   */
  async goto(): Promise<void> {
    await super.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * Click sign up button
   */
  async clickSignUp(): Promise<void> {
    await this.clickElement(this.signUpButton);
  }

  /**
   * Click login button
   */
  async clickLogin(): Promise<void> {
    await this.clickElement(this.loginButton);
  }

  /**
   * Click search jobs button
   */
  async clickSearchJobs(): Promise<void> {
    await this.clickElement(this.searchJobsButton);
  }

  /**
   * Verify home page is loaded
   */
  async verifyHomePageLoaded(): Promise<void> {
    await this.waitForVisible(this.heroSection);
    await this.waitForVisible(this.signUpButton);
    await this.waitForVisible(this.loginButton);
  }

  /**
   * Get featured jobs count
   */
  async getFeaturedJobsCount(): Promise<number> {
    await this.waitForVisible(this.featuredJobs);
    const jobCards = this.featuredJobs.locator('[data-testid="job-card"]');
    return await jobCards.count();
  }

  /**
   * Click on a specific featured job
   */
  async clickFeaturedJob(index: number): Promise<void> {
    const jobCards = this.featuredJobs.locator('[data-testid="job-card"]');
    const jobCard = jobCards.nth(index);
    await this.clickElement(jobCard);
  }

  /**
   * Navigate using menu
   */
  async navigateToPage(pageName: string): Promise<void> {
    const menuItem = this.navigationMenu.getByRole('link', { name: pageName });
    await this.clickElement(menuItem);
  }

  /**
   * Verify navigation menu is present
   */
  async verifyNavigationMenu(): Promise<void> {
    await this.waitForVisible(this.navigationMenu);
  }
}