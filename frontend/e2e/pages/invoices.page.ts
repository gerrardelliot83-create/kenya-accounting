import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Invoices Page
 */
export class InvoicesPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly invoiceTable: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly firstInvoiceRow: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.createButton = page.locator('button:has-text("New Invoice")');
    this.invoiceTable = page.locator('table');
    this.searchInput = page.locator('input[placeholder*="Search"]');
    this.statusFilter = page.locator('[role="combobox"]').first();
    this.firstInvoiceRow = page.locator('tbody tr').first();
  }

  async goto() {
    await this.page.goto('/invoices');
  }

  async clickCreateInvoice() {
    await this.createButton.click();
  }

  async createInvoice(data: {
    contactName?: string;
    items: Array<{ description: string; quantity: number; price: number }>;
  }) {
    await this.createButton.click();
    await this.page.waitForURL('**/invoices/new');

    // Select contact if provided
    if (data.contactName) {
      const contactSelect = this.page.locator('[data-testid="contact-select"]').or(
        this.page.locator('button:has-text("Select contact"), button:has-text("Choose contact")').first()
      );
      await contactSelect.click();
      await this.page.locator(`text=${data.contactName}`).first().click();
    }

    // Add line items
    for (let i = 0; i < data.items.length; i++) {
      const item = data.items[i];

      // Click add item button if not the first item
      if (i > 0) {
        await this.page.locator('button:has-text("Add Item")').click();
      }

      // Fill item details - use nth selectors for multiple items
      await this.page.locator('input[name="description"]').nth(i).fill(item.description);
      await this.page.locator('input[name="quantity"]').nth(i).fill(item.quantity.toString());
      await this.page.locator('input[name="unit_price"], input[name="price"]').nth(i).fill(item.price.toString());
    }

    // Save the invoice
    await this.page.locator('button:has-text("Save"), button:has-text("Create")').click();
  }

  async filterByStatus(status: string) {
    await this.statusFilter.click();
    await this.page.locator(`text=${status}`).click();
  }

  async clickFirstInvoice() {
    await this.firstInvoiceRow.click();
  }

  async getInvoiceCount() {
    return await this.page.locator('tbody tr').count();
  }

  async isEmptyState() {
    return await this.page.locator('text=No invoices found').isVisible();
  }
}
