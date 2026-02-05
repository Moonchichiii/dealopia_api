import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load home page with optimized API calls', async ({ page }) => {
    // Start API request monitoring
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });

    await page.goto('/');

    // Verify hero section is visible
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByText('Sustainable Shopping')).toBeVisible();

    // Verify search functionality
    const searchInput = page.getByPlaceholder('Search for deals');
    await searchInput.click();
    await searchInput.fill('test');
    
    // Verify debounced API call
    await page.waitForTimeout(300); // Wait for debounce
    const searchRequests = apiRequests.filter(url => url.includes('/api/search'));
    expect(searchRequests.length).toBeLessThanOrEqual(1);

    // Test lazy loading of deals
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Verify only one batch of deals is loaded
    const dealRequests = apiRequests.filter(url => url.includes('/api/deals'));
    expect(dealRequests.length).toBeLessThanOrEqual(1);
  });

  test('should handle geolocation efficiently', async ({ page }) => {
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });

    // Mock geolocation
    await page.setGeolocation({ latitude: 51.5074, longitude: -0.1278 });

    await page.goto('/');
    await page.click('text=Near Me');

    // Verify single location-based API call
    const locationRequests = apiRequests.filter(url => url.includes('/api/nearby'));
    expect(locationRequests.length).toBe(1);
  });

  test('should optimize image loading', async ({ page }) => {
    const imageRequests = [];
    page.on('request', request => {
      if (request.url().includes('.jpg') || request.url().includes('.png')) {
        imageRequests.push(request.url());
      }
    });

    await page.goto('/');

    // Scroll to trigger lazy loading
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Verify images are loaded with correct dimensions
    for (const request of imageRequests) {
      expect(request).toMatch(/w=\d+/); // Check for width parameter
      expect(request).toMatch(/q=\d+/); // Check for quality parameter
    }
  });
});