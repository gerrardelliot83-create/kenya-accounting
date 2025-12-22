import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Admin Portal
 */
export class AdminPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly totalBusinessesCard: Locator;
  readonly businessesLink: Locator;
  readonly usersLink: Locator;
  readonly auditLogsLink: Locator;
  readonly systemHealthLink: Locator;
  readonly businessesTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.totalBusinessesCard = page.locator('[data-testid="total-businesses"]');
    this.businessesLink = page.locator('a:has-text("Businesses")');
    this.usersLink = page.locator('a:has-text("Users")');
    this.auditLogsLink = page.locator('a:has-text("Audit Logs")');
    this.systemHealthLink = page.locator('a:has-text("System Health")');
    this.businessesTable = page.locator('table');
  }

  async goto() {
    await this.page.goto('/admin');
  }

  async gotoBusinesses() {
    await this.page.goto('/admin/businesses');
  }

  async gotoUsers() {
    await this.page.goto('/admin/users');
  }

  async gotoAuditLogs() {
    await this.page.goto('/admin/audit-logs');
  }

  async gotoSystemHealth() {
    await this.page.goto('/admin/system');
  }

  async viewBusinessDetail(businessName: string) {
    await this.gotoBusinesses();
    await this.page.locator(`tr:has-text("${businessName}")`).first().click();
  }

  async getBusinessCount() {
    return await this.page.locator('tbody tr').count();
  }

  async checkSensitiveDataMasked(selector: string) {
    const text = await this.page.locator(selector).textContent();
    return text?.includes('*') || false;
  }

  async getTotalBusinesses() {
    const text = await this.totalBusinessesCard.textContent();
    return parseInt(text?.replace(/\D/g, '') || '0');
  }
}
