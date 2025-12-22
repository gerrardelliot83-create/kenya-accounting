import { test, expect } from './fixtures/auth';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';

test.describe('Authentication', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('business@example.com', 'BusinessPass123');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error with invalid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('business@example.com', 'wrongpassword');

    // Should show error message
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should show validation error for invalid email format', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.emailInput.fill('invalid-email');
    await loginPage.passwordInput.fill('password123');
    await loginPage.submitButton.click();

    // Should show validation error
    await expect(page.locator('text=valid email')).toBeVisible();
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/invoices');

    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should logout successfully', async ({ authenticatedPage }) => {
    const dashboardPage = new DashboardPage(authenticatedPage);

    // Verify we're on dashboard
    await expect(authenticatedPage).toHaveURL(/.*\/dashboard/);

    // Logout (try multiple possible logout mechanisms)
    try {
      // Try user menu approach
      await dashboardPage.userMenu.click();
      await dashboardPage.logoutButton.click();
    } catch {
      // Fallback: try direct logout link
      await authenticatedPage.locator('button:has-text("Logout"), a:has-text("Logout")').first().click();
    }

    // Should redirect to login
    await expect(authenticatedPage).toHaveURL(/.*\/login/, { timeout: 10000 });
  });

  test('should persist authentication across page navigation', async ({ authenticatedPage }) => {
    // Verify we're authenticated
    await expect(authenticatedPage).toHaveURL(/.*\/dashboard/);

    // Navigate to different pages
    await authenticatedPage.goto('/invoices');
    await expect(authenticatedPage).toHaveURL(/.*\/invoices/);

    await authenticatedPage.goto('/expenses');
    await expect(authenticatedPage).toHaveURL(/.*\/expenses/);

    await authenticatedPage.goto('/contacts');
    await expect(authenticatedPage).toHaveURL(/.*\/contacts/);

    // Should still be authenticated (not redirected to login)
    await expect(authenticatedPage).not.toHaveURL(/.*\/login/);
  });

  test('should prevent access to admin portal for non-admin users', async ({ authenticatedPage }) => {
    // Try to access admin portal as regular business user
    await authenticatedPage.goto('/admin');

    // Should either redirect or show forbidden message
    // Not staying on /admin path
    const currentUrl = authenticatedPage.url();
    expect(currentUrl).not.toContain('/admin');
  });
});
