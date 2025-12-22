import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Dashboard Page
 */
export class DashboardPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.userMenu = page.locator('[data-testid="user-menu"]').or(page.locator('button:has-text("account"), button:has-text("user")').first());
    this.logoutButton = page.locator('text=Logout, text=Sign out').first();
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }

  async getPageTitle() {
    return await this.pageTitle.textContent();
  }
}
