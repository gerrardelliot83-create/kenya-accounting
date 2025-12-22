import { test as base, Page } from '@playwright/test';

/**
 * Extend base test with authentication fixtures for different user roles
 */
export const test = base.extend<{
  authenticatedPage: Page;
  adminPage: Page;
  onboardingPage: Page;
  supportPage: Page;
}>({
  /**
   * Fixture for a business user with standard access
   */
  authenticatedPage: async ({ page }, use) => {
    // Login as business user
    await page.goto('/login');
    await page.fill('input[type="email"]', 'business@example.com');
    await page.fill('input[type="password"]', 'BusinessPass123');
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');

    await use(page);
  },

  /**
   * Fixture for a system admin user with full access
   */
  adminPage: async ({ page }, use) => {
    // Login as system admin
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'AdminPass123');
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');

    await use(page);
  },

  /**
   * Fixture for an onboarding agent with onboarding portal access
   */
  onboardingPage: async ({ page }, use) => {
    // Login as onboarding agent
    await page.goto('/login');
    await page.fill('input[type="email"]', 'onboarding@example.com');
    await page.fill('input[type="password"]', 'OnboardPass123');
    await page.click('button[type="submit"]');

    // Wait for navigation (could be dashboard or onboarding portal)
    await page.waitForURL(/\/(dashboard|onboarding)/);

    await use(page);
  },

  /**
   * Fixture for a support agent with support portal access
   */
  supportPage: async ({ page }, use) => {
    // Login as support agent
    await page.goto('/login');
    await page.fill('input[type="email"]', 'support@example.com');
    await page.fill('input[type="password"]', 'SupportPass123');
    await page.click('button[type="submit"]');

    // Wait for navigation (could be dashboard or support portal)
    await page.waitForURL(/\/(dashboard|support-portal)/);

    await use(page);
  },
});

export { expect } from '@playwright/test';
