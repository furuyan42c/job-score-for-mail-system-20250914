import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Jobs Page Object Model (Job Search, Listings, Details)
 */
export class JobsPage extends BasePage {
  // Search elements
  readonly searchContainer: Locator;
  readonly searchInput: Locator;
  readonly locationInput: Locator;
  readonly searchButton: Locator;
  readonly searchFilters: Locator;
  readonly clearFiltersButton: Locator;

  // Filter elements
  readonly salaryFilter: Locator;
  readonly jobTypeFilter: Locator;
  readonly experienceFilter: Locator;
  readonly companyFilter: Locator;
  readonly datePostedFilter: Locator;
  readonly applyFiltersButton: Locator;

  // Results elements
  readonly jobListings: Locator;
  readonly jobCards: Locator;
  readonly noResultsMessage: Locator;
  readonly loadingSpinner: Locator;
  readonly paginationContainer: Locator;
  readonly resultsCount: Locator;

  // Sort and view options
  readonly sortDropdown: Locator;
  readonly viewToggle: Locator; // List vs Grid view
  readonly saveSearchButton: Locator;

  // Job detail elements
  readonly jobDetailContainer: Locator;
  readonly jobTitle: Locator;
  readonly companyName: Locator;
  readonly jobLocation: Locator;
  readonly jobSalary: Locator;
  readonly jobDescription: Locator;
  readonly jobRequirements: Locator;
  readonly applyButton: Locator;
  readonly saveJobButton: Locator;
  readonly shareJobButton: Locator;
  readonly backToResultsButton: Locator;

  constructor(page: Page) {
    super(page);

    // Search elements
    this.searchContainer = this.getByTestId('search-container');
    this.searchInput = this.getByTestId('job-search-input');
    this.locationInput = this.getByTestId('location-input');
    this.searchButton = this.getByTestId('search-button');
    this.searchFilters = this.getByTestId('search-filters');
    this.clearFiltersButton = this.getByTestId('clear-filters');

    // Filter elements
    this.salaryFilter = this.getByTestId('salary-filter');
    this.jobTypeFilter = this.getByTestId('job-type-filter');
    this.experienceFilter = this.getByTestId('experience-filter');
    this.companyFilter = this.getByTestId('company-filter');
    this.datePostedFilter = this.getByTestId('date-posted-filter');
    this.applyFiltersButton = this.getByTestId('apply-filters');

    // Results elements
    this.jobListings = this.getByTestId('job-listings');
    this.jobCards = this.getByTestId('job-card');
    this.noResultsMessage = this.getByTestId('no-results');
    this.loadingSpinner = this.getByTestId('loading-spinner');
    this.paginationContainer = this.getByTestId('pagination');
    this.resultsCount = this.getByTestId('results-count');

    // Sort and view options
    this.sortDropdown = this.getByTestId('sort-dropdown');
    this.viewToggle = this.getByTestId('view-toggle');
    this.saveSearchButton = this.getByTestId('save-search');

    // Job detail elements
    this.jobDetailContainer = this.getByTestId('job-detail');
    this.jobTitle = this.getByTestId('job-title');
    this.companyName = this.getByTestId('company-name');
    this.jobLocation = this.getByTestId('job-location');
    this.jobSalary = this.getByTestId('job-salary');
    this.jobDescription = this.getByTestId('job-description');
    this.jobRequirements = this.getByTestId('job-requirements');
    this.applyButton = this.getByTestId('apply-button');
    this.saveJobButton = this.getByTestId('save-job-button');
    this.shareJobButton = this.getByTestId('share-job-button');
    this.backToResultsButton = this.getByTestId('back-to-results');
  }

  /**
   * Navigate to jobs page
   */
  async goto(): Promise<void> {
    await super.goto('/jobs');
    await this.waitForPageLoad();
  }

  /**
   * Perform job search
   */
  async searchJobs(keyword: string, location: string = ''): Promise<void> {
    await this.fillInput(this.searchInput, keyword);

    if (location) {
      await this.fillInput(this.locationInput, location);
    }

    await this.clickElement(this.searchButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Apply salary filter
   */
  async applySalaryFilter(minSalary: string, maxSalary: string = ''): Promise<void> {
    await this.clickElement(this.salaryFilter);

    const minInput = this.salaryFilter.locator('[data-testid="min-salary"]');
    const maxInput = this.salaryFilter.locator('[data-testid="max-salary"]');

    await this.fillInput(minInput, minSalary);

    if (maxSalary) {
      await this.fillInput(maxInput, maxSalary);
    }

    await this.clickElement(this.applyFiltersButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Apply job type filter
   */
  async applyJobTypeFilter(jobType: string): Promise<void> {
    await this.clickElement(this.jobTypeFilter);

    const jobTypeOption = this.jobTypeFilter.locator(`[data-value="${jobType}"]`);
    await this.clickElement(jobTypeOption);

    await this.clickElement(this.applyFiltersButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Apply experience filter
   */
  async applyExperienceFilter(experience: string): Promise<void> {
    await this.clickElement(this.experienceFilter);

    const experienceOption = this.experienceFilter.locator(`[data-value="${experience}"]`);
    await this.clickElement(experienceOption);

    await this.clickElement(this.applyFiltersButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Clear all filters
   */
  async clearAllFilters(): Promise<void> {
    await this.clickElement(this.clearFiltersButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Get number of job results
   */
  async getJobCount(): Promise<number> {
    await this.waitForVisible(this.jobListings);
    return await this.jobCards.count();
  }

  /**
   * Get results count text
   */
  async getResultsCountText(): Promise<string> {
    await this.waitForVisible(this.resultsCount);
    return await this.resultsCount.textContent() || '';
  }

  /**
   * Click on a specific job card
   */
  async clickJobCard(index: number): Promise<void> {
    const jobCard = this.jobCards.nth(index);
    await this.clickElement(jobCard);
    await this.waitForVisible(this.jobDetailContainer);
  }

  /**
   * Get job card information
   */
  async getJobCardInfo(index: number): Promise<{
    title: string;
    company: string;
    location: string;
    salary?: string;
  }> {
    const jobCard = this.jobCards.nth(index);

    const title = await jobCard.locator('[data-testid="card-job-title"]').textContent() || '';
    const company = await jobCard.locator('[data-testid="card-company"]').textContent() || '';
    const location = await jobCard.locator('[data-testid="card-location"]').textContent() || '';
    const salaryElement = jobCard.locator('[data-testid="card-salary"]');
    const salary = await salaryElement.isVisible() ? await salaryElement.textContent() || undefined : undefined;

    return { title, company, location, salary };
  }

  /**
   * Sort jobs by criteria
   */
  async sortJobsBy(criteria: 'relevance' | 'date' | 'salary' | 'company'): Promise<void> {
    await this.clickElement(this.sortDropdown);

    const sortOption = this.sortDropdown.locator(`[data-value="${criteria}"]`);
    await this.clickElement(sortOption);

    await this.waitForLoadingToComplete();
  }

  /**
   * Toggle view between list and grid
   */
  async toggleView(): Promise<void> {
    await this.clickElement(this.viewToggle);
    await this.waitForLoadingToComplete();
  }

  /**
   * Navigate to next page of results
   */
  async goToNextPage(): Promise<void> {
    const nextButton = this.paginationContainer.locator('[data-testid="next-page"]');
    await this.clickElement(nextButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Navigate to previous page of results
   */
  async goToPreviousPage(): Promise<void> {
    const prevButton = this.paginationContainer.locator('[data-testid="prev-page"]');
    await this.clickElement(prevButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Apply to a job
   */
  async applyToJob(): Promise<void> {
    await this.waitForVisible(this.applyButton);
    await this.clickElement(this.applyButton);
  }

  /**
   * Save a job
   */
  async saveJob(): Promise<void> {
    await this.clickElement(this.saveJobButton);
  }

  /**
   * Share a job
   */
  async shareJob(): Promise<void> {
    await this.clickElement(this.shareJobButton);
  }

  /**
   * Go back to job results
   */
  async backToResults(): Promise<void> {
    await this.clickElement(this.backToResultsButton);
    await this.waitForVisible(this.jobListings);
  }

  /**
   * Get job detail information
   */
  async getJobDetailInfo(): Promise<{
    title: string;
    company: string;
    location: string;
    salary?: string;
    description: string;
    requirements: string;
  }> {
    await this.waitForVisible(this.jobDetailContainer);

    const title = await this.jobTitle.textContent() || '';
    const company = await this.companyName.textContent() || '';
    const location = await this.jobLocation.textContent() || '';
    const salaryText = await this.jobSalary.isVisible() ? await this.jobSalary.textContent() || undefined : undefined;
    const description = await this.jobDescription.textContent() || '';
    const requirements = await this.jobRequirements.textContent() || '';

    return {
      title,
      company,
      location,
      salary: salaryText,
      description,
      requirements
    };
  }

  /**
   * Save current search
   */
  async saveCurrentSearch(searchName: string): Promise<void> {
    await this.clickElement(this.saveSearchButton);

    // Fill search name in modal
    const nameInput = this.page.getByTestId('search-name-input');
    await this.fillInput(nameInput, searchName);

    const saveButton = this.page.getByTestId('save-search-confirm');
    await this.clickElement(saveButton);
  }

  /**
   * Verify jobs page is loaded
   */
  async verifyJobsPageLoaded(): Promise<void> {
    await this.waitForVisible(this.searchContainer);
    await this.waitForVisible(this.searchInput);
    await this.waitForVisible(this.searchButton);
  }

  /**
   * Verify no results message is displayed
   */
  async verifyNoResults(): Promise<void> {
    await this.waitForVisible(this.noResultsMessage);
  }

  /**
   * Verify job detail page is loaded
   */
  async verifyJobDetailLoaded(): Promise<void> {
    await this.waitForVisible(this.jobDetailContainer);
    await this.waitForVisible(this.jobTitle);
    await this.waitForVisible(this.companyName);
    await this.waitForVisible(this.applyButton);
  }

  /**
   * Wait for search results to load
   */
  async waitForSearchResults(): Promise<void> {
    await this.waitForLoadingToComplete();

    // Wait for either results or no results message
    await this.page.waitForFunction(() => {
      const jobListings = document.querySelector('[data-testid="job-listings"]');
      const noResults = document.querySelector('[data-testid="no-results"]');
      return (jobListings && jobListings.children.length > 0) || noResults;
    }, { timeout: 15000 });
  }
}