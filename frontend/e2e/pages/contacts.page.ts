import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Contacts Page
 */
export class ContactsPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly contactsTable: Locator;
  readonly searchInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.createButton = page.locator('button:has-text("Add Contact"), button:has-text("New Contact")').first();
    this.contactsTable = page.locator('table');
    this.searchInput = page.locator('input[placeholder*="Search"]');
  }

  async goto() {
    await this.page.goto('/contacts');
  }

  async createContact(data: {
    name: string;
    email?: string;
    phone?: string;
    type: 'customer' | 'vendor';
  }) {
    await this.createButton.click();

    // Fill contact form
    await this.page.locator('input[name="name"]').fill(data.name);

    if (data.email) {
      await this.page.locator('input[name="email"]').fill(data.email);
    }

    if (data.phone) {
      await this.page.locator('input[name="phone"]').fill(data.phone);
    }

    // Select contact type
    const typeSelect = this.page.locator('[data-testid="contact-type-select"]').or(
      this.page.locator('button:has-text("Select type")').first()
    );
    await typeSelect.click();
    await this.page.locator(`text=${data.type}`).first().click();

    // Save
    await this.page.locator('button:has-text("Save"), button:has-text("Create")').click();
  }

  async searchContact(searchTerm: string) {
    await this.searchInput.fill(searchTerm);
  }
}
