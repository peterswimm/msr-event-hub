/**
 * Visual Regression Tests for Adaptive Card Components
 * Uses Playwright for screenshot comparison
 */

import { test, expect } from '@playwright/test';

test.describe('Adaptive Card Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the test page or storybook
    await page.goto('http://localhost:5173/chat'); // Adjust URL as needed
  });

  test('Welcome card renders correctly', async ({ page }) => {
    // Wait for the welcome card to load
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    // Take screenshot of the welcome card
    const welcomeCard = page.locator('.adaptive-card-container').first();
    await expect(welcomeCard).toHaveScreenshot('welcome-card.png', {
      maxDiffPixels: 100, // Allow minor rendering differences
    });
  });

  test('Project carousel renders correctly', async ({ page }) => {
    // Trigger project search or browse action
    await page.click('button:has-text("Browse All Projects")');
    
    // Wait for carousel to appear
    await page.waitForSelector('[role="region"][aria-roledescription="carousel"]', { timeout: 5000 });
    
    const carousel = page.locator('[role="region"][aria-roledescription="carousel"]').first();
    await expect(carousel).toHaveScreenshot('project-carousel.png', {
      maxDiffPixels: 100,
    });
  });

  test('Project carousel navigation animation', async ({ page }) => {
    // Trigger carousel display
    await page.click('button:has-text("Browse All Projects")');
    await page.waitForSelector('[role="region"][aria-roledescription="carousel"]');
    
    // Take initial screenshot
    const carousel = page.locator('[role="region"][aria-roledescription="carousel"]').first();
    await expect(carousel).toHaveScreenshot('carousel-slide-1.png');
    
    // Navigate to next slide
    await page.click('button[aria-label*="Next project"]');
    await page.waitForTimeout(500); // Wait for animation
    
    // Take screenshot of second slide
    await expect(carousel).toHaveScreenshot('carousel-slide-2.png');
  });

  test('Project detail card renders correctly', async ({ page }) => {
    // Search for a specific project
    await page.fill('input[placeholder*="Ask"]', 'Tell me about AI projects');
    await page.press('input[placeholder*="Ask"]', 'Enter');
    
    // Wait for project details card
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const detailCard = page.locator('.adaptive-card-container').first();
    await expect(detailCard).toHaveScreenshot('project-detail-card.png', {
      maxDiffPixels: 100,
    });
  });

  test('Form card renders correctly', async ({ page }) => {
    // This test assumes a form card is available in the chat
    // Adjust based on actual implementation
    await page.fill('input[placeholder*="Ask"]', 'I want to provide feedback');
    await page.press('input[placeholder*="Ask"]', 'Enter');
    
    await page.waitForSelector('input[type="text"]', { timeout: 5000 });
    
    const formCard = page.locator('.adaptive-card-container').first();
    await expect(formCard).toHaveScreenshot('feedback-form-card.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dark theme rendering', async ({ page }) => {
    // Toggle dark theme if available
    await page.emulateMedia({ colorScheme: 'dark' });
    
    await page.reload();
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('welcome-card-dark.png', {
      maxDiffPixels: 100,
    });
  });

  test('Responsive layout - mobile view', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    
    await page.reload();
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('welcome-card-mobile.png', {
      maxDiffPixels: 100,
    });
  });

  test('Responsive layout - tablet view', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    
    await page.reload();
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('welcome-card-tablet.png', {
      maxDiffPixels: 100,
    });
  });

  test('Hover states on interactive elements', async ({ page }) => {
    // Wait for card with actions
    await page.waitForSelector('button', { timeout: 5000 });
    
    const button = page.locator('button').first();
    await button.hover();
    
    // Wait for hover animation
    await page.waitForTimeout(200);
    
    await expect(button).toHaveScreenshot('button-hover-state.png', {
      maxDiffPixels: 50,
    });
  });

  test('Focus states for keyboard navigation', async ({ page }) => {
    await page.waitForSelector('button', { timeout: 5000 });
    
    // Tab to first button
    await page.keyboard.press('Tab');
    
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toHaveScreenshot('button-focus-state.png', {
      maxDiffPixels: 50,
    });
  });

  test('Error state rendering', async ({ page }) => {
    // Trigger error scenario (e.g., network failure)
    await page.route('**/api/chat', route => route.abort());
    
    await page.fill('input[placeholder*="Ask"]', 'Test error');
    await page.press('input[placeholder*="Ask"]', 'Enter');
    
    // Wait for error message
    await page.waitForSelector('text=/error|failed|try again/i', { timeout: 5000 });
    
    const errorContainer = page.locator('.chat-container').first();
    await expect(errorContainer).toHaveScreenshot('error-state.png', {
      maxDiffPixels: 100,
    });
  });

  test('Loading state animation', async ({ page }) => {
    // Delay response to capture loading state
    await page.route('**/api/chat', route => {
      setTimeout(() => route.continue(), 2000);
    });
    
    await page.fill('input[placeholder*="Ask"]', 'Loading test');
    await page.press('input[placeholder*="Ask"]', 'Enter');
    
    // Capture loading spinner/skeleton
    await page.waitForSelector('[role="progressbar"], .loading, .skeleton', { timeout: 1000 });
    
    const loadingState = page.locator('.chat-container').first();
    await expect(loadingState).toHaveScreenshot('loading-state.png', {
      maxDiffPixels: 100,
    });
  });
});

test.describe('Cross-browser Visual Tests', () => {
  test('Renders consistently in Chromium', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Chromium-only test');
    
    await page.goto('http://localhost:5173/chat');
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('card-chromium.png');
  });

  test('Renders consistently in Firefox', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Firefox-only test');
    
    await page.goto('http://localhost:5173/chat');
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('card-firefox.png');
  });

  test('Renders consistently in WebKit', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'WebKit-only test');
    
    await page.goto('http://localhost:5173/chat');
    await page.waitForSelector('.adaptive-card-container', { timeout: 5000 });
    
    const card = page.locator('.adaptive-card-container').first();
    await expect(card).toHaveScreenshot('card-webkit.png');
  });
});
