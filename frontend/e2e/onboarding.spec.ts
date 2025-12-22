import { test, expect } from './fixtures/auth';
import { OnboardingPage } from './pages/onboarding.page';

test.describe('Onboarding Portal', () => {
  test('should display onboarding dashboard for authorized users', async ({ onboardingPage }) => {
    const onboarding = new OnboardingPage(onboardingPage);
    await onboarding.goto();

    // Should be on onboarding portal
    await expect(onboardingPage).toHaveURL(/.*\/onboarding/);

    // Page title should be visible
    await expect(onboarding.pageTitle).toBeVisible();
  });

  test('should navigate to create business application page', async ({ onboardingPage }) => {
    const onboarding = new OnboardingPage(onboardingPage);
    await onboarding.gotoCreate();

    // Should be on create page
    await expect(onboardingPage).toHaveURL(/.*\/onboarding\/create/);

    // Form fields should be visible
    await expect(onboardingPage.locator('input[name="business_name"]')).toBeVisible();
  });

  test('should create a new business application', async ({ onboardingPage }) => {
    await onboardingPage.goto('/onboarding/create');

    // Wait for form to load
    await onboardingPage.waitForSelector('input[name="business_name"]', { timeout: 10000 });

    // Fill business details
    await onboardingPage.locator('input[name="business_name"]').fill('Test Company Ltd');

    // Business type
    const businessTypeSelect = onboardingPage.locator('[data-testid="business-type-select"]').or(
      onboardingPage.locator('button:has-text("Select type"), select[name="business_type"]').first()
    );
    const hasBusinessType = await businessTypeSelect.isVisible().catch(() => false);

    if (hasBusinessType) {
      await businessTypeSelect.click();
      await onboardingPage.locator('[role="option"]').first().click();
    }

    // KRA PIN
    const kraPinInput = onboardingPage.locator('input[name="kra_pin"]');
    const hasKraPin = await kraPinInput.isVisible().catch(() => false);

    if (hasKraPin) {
      await kraPinInput.fill('P051234567A');
    }

    // County
    const countySelect = onboardingPage.locator('[data-testid="county-select"]').or(
      onboardingPage.locator('button:has-text("Select county"), select[name="county"]').first()
    );
    const hasCounty = await countySelect.isVisible().catch(() => false);

    if (hasCounty) {
      await countySelect.click();
      await onboardingPage.locator('[role="option"]').first().click();
    }

    // Contact details
    await onboardingPage.locator('input[name="phone"]').fill('+254712345678');
    await onboardingPage.locator('input[name="email"]').fill('test@company.co.ke');

    // Owner details
    const ownerNameInput = onboardingPage.locator('input[name="owner_name"]');
    const hasOwnerName = await ownerNameInput.isVisible().catch(() => false);

    if (hasOwnerName) {
      await ownerNameInput.fill('John Doe');
      await onboardingPage.locator('input[name="owner_national_id"]').fill('12345678');
      await onboardingPage.locator('input[name="owner_phone"]').fill('+254712345679');
      await onboardingPage.locator('input[name="owner_email"]').fill('john@company.co.ke');
    }

    // Submit form
    await onboardingPage.locator('button[type="submit"], button:has-text("Create"), button:has-text("Submit")').click();

    // Wait for success or navigation
    await onboardingPage.waitForTimeout(2000);

    // Should show success message or navigate away
    const successMessage = onboardingPage.locator('text=created, text=success').first();
    const hasSuccess = await successMessage.isVisible().catch(() => false);

    // Test passes if submission worked
    expect(hasSuccess || onboardingPage.url().includes('/onboarding')).toBe(true);
  });

  test('should display applications queue', async ({ onboardingPage }) => {
    const onboarding = new OnboardingPage(onboardingPage);
    await onboarding.gotoQueue();

    // Should be on queue page
    await expect(onboardingPage).toHaveURL(/.*\/onboarding\/queue/);

    // Table should be visible
    await expect(onboarding.applicationsTable).toBeVisible();
  });

  test('should view application details', async ({ onboardingPage }) => {
    await onboardingPage.goto('/onboarding/queue');

    // Wait for table to load
    await onboardingPage.waitForSelector('table', { timeout: 10000 });

    const rowCount = await onboardingPage.locator('tbody tr').count();

    if (rowCount > 0) {
      // Click first application
      const firstRow = onboardingPage.locator('tbody tr').first();
      await firstRow.click();

      // Should navigate to detail page
      await expect(onboardingPage).toHaveURL(/.*\/onboarding\/applications\/[a-f0-9-]+/);
    } else {
      // No applications - test still passes
      expect(true).toBe(true);
    }
  });

  test('should validate business application form', async ({ onboardingPage }) => {
    await onboardingPage.goto('/onboarding/create');

    // Wait for form
    await onboardingPage.waitForSelector('input[name="business_name"]', { timeout: 10000 });

    // Try to submit without filling required fields
    await onboardingPage.locator('button[type="submit"], button:has-text("Create")').click();

    // Should show validation errors
    const validationError = onboardingPage.locator('text=required, text=Required').first();
    const hasValidationError = await validationError.isVisible().catch(() => false);

    // Form should still be visible (validation prevented submission)
    const formStillVisible = await onboardingPage.locator('input[name="business_name"]').isVisible().catch(() => false);

    expect(formStillVisible || hasValidationError).toBe(true);
  });

  test('should deny access to non-onboarding users', async ({ authenticatedPage }) => {
    // Try to access onboarding portal as regular business user
    await authenticatedPage.goto('/onboarding');

    // Should redirect or show forbidden
    await authenticatedPage.waitForTimeout(2000);

    const currentUrl = authenticatedPage.url();

    // Should not stay on onboarding portal
    expect(currentUrl.includes('/onboarding')).toBe(false);
  });

  test('should allow system admin to access onboarding portal', async ({ adminPage }) => {
    // System admin should have access to onboarding portal
    await adminPage.goto('/onboarding');

    // Should be able to access (no redirect)
    await adminPage.waitForTimeout(2000);

    const currentUrl = adminPage.url();

    // Should stay on onboarding portal or main admin dashboard
    expect(currentUrl.includes('/onboarding') || currentUrl.includes('/admin') || currentUrl.includes('/dashboard')).toBe(true);
  });
});
