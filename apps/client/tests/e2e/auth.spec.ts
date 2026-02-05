import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should handle login efficiently', async ({ page }) => {
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });

    await page.goto('/signin');

    // Fill login form
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Verify single login request
    const authRequests = apiRequests.filter(url => url.includes('/api/auth'));
    expect(authRequests.length).toBe(1);

    // Verify token storage
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();
  });

  test('should maintain session efficiently', async ({ page }) => {
    // Mock authenticated session
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-token');
    });

    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });

    await page.goto('/dashboard');

    // Verify no unnecessary auth checks
    const authRequests = apiRequests.filter(url => url.includes('/api/auth'));
    expect(authRequests.length).toBe(0);
  });
});