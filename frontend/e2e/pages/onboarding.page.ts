import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Onboarding Portal
 */
export class OnboardingPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createApplicationButton: Locator;
  readonly queueLink: Locator;
  readonly applicationsTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.createApplicationButton = page.locator('button:has-text("Create Application"), a:has-text("Create Business")').first();
    this.queueLink = page.locator('a:has-text("Queue")');
    this.applicationsTable = page.locator('table');
  }

  async goto() {
    await this.page.goto('/onboarding');
  }

  async gotoQueue() {
    await this.page.goto('/onboarding/queue');
  }

  async gotoCreate() {
    await this.page.goto('/onboarding/create');
  }

  async createBusinessApplication(data: {
    businessName: string;
    businessType: string;
    kraPin: string;
    county: string;
    phone: string;
    email: string;
    ownerName: string;
    ownerNationalId: string;
    ownerPhone: string;
    ownerEmail: string;
  }) {
    // Navigate to create page
    await this.gotoCreate();

    // Fill business details
    await this.page.locator('input[name="business_name"]').fill(data.businessName);

    // Select business type
    const businessTypeSelect = this.page.locator('[data-testid="business-type-select"]').or(
      this.page.locator('button:has-text("Select type")').first()
    );
    await businessTypeSelect.click();
    await this.page.locator(`text=${data.businessType}`).first().click();

    await this.page.locator('input[name="kra_pin"]').fill(data.kraPin);

    // Select county
    const countySelect = this.page.locator('[data-testid="county-select"]').or(
      this.page.locator('button:has-text("Select county")').first()
    );
    await countySelect.click();
    await this.page.locator(`text=${data.county}`).first().click();

    await this.page.locator('input[name="phone"]').fill(data.phone);
    await this.page.locator('input[name="email"]').fill(data.email);

    // Fill owner details
    await this.page.locator('input[name="owner_name"]').fill(data.ownerName);
    await this.page.locator('input[name="owner_national_id"]').fill(data.ownerNationalId);
    await this.page.locator('input[name="owner_phone"]').fill(data.ownerPhone);
    await this.page.locator('input[name="owner_email"]').fill(data.ownerEmail);

    // Submit
    await this.page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Submit")').click();
  }

  async viewApplication(businessName: string) {
    await this.page.locator(`tr:has-text("${businessName}")`).first().click();
  }

  async getApplicationCount() {
    return await this.page.locator('tbody tr').count();
  }
}
