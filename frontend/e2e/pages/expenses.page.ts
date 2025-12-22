import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Expenses Page
 */
export class ExpensesPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly expensesTable: Locator;
  readonly categoryFilter: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.locator('h1');
    this.createButton = page.locator('button:has-text("Add Expense"), button:has-text("New Expense")').first();
    this.expensesTable = page.locator('table');
    this.categoryFilter = page.locator('[data-testid="category-filter"]').or(
      page.locator('button:has-text("Category")').first()
    );
  }

  async goto() {
    await this.page.goto('/expenses');
  }

  async createExpense(data: {
    description: string;
    amount: number;
    category: string;
    paymentMethod: string;
  }) {
    await this.createButton.click();

    // Fill expense form
    await this.page.locator('input[name="description"]').fill(data.description);
    await this.page.locator('input[name="amount"]').fill(data.amount.toString());

    // Select category
    const categorySelect = this.page.locator('[data-testid="category-select"]').or(
      this.page.locator('button:has-text("Select category")').first()
    );
    await categorySelect.click();
    await this.page.locator(`text=${data.category}`).first().click();

    // Select payment method
    const paymentMethodSelect = this.page.locator('[data-testid="payment-method-select"]').or(
      this.page.locator('button:has-text("Select payment")').first()
    );
    await paymentMethodSelect.click();
    await this.page.locator(`text=${data.paymentMethod}`).first().click();

    // Save
    await this.page.locator('button:has-text("Save"), button:has-text("Create")').click();
  }

  async filterByCategory(category: string) {
    await this.categoryFilter.click();
    await this.page.locator(`text=${category}`).click();
  }

  async getExpenseCount() {
    return await this.page.locator('tbody tr').count();
  }
}
