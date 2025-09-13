/**
 * Test setup configuration for Monthly Swing Trading frontend
 *
 * @description Global test setup including DOM mocking and test utilities.
 * This file is executed before each test file.
 */

import '@testing-library/jest-dom';
import { beforeEach, afterEach, jest } from 'bun:test';

// Setup DOM environment
import { Window } from 'happy-dom';

// Create a global DOM window for testing
const window = new Window();
const document = window.document;

// Set global variables
global.window = window as any;
global.document = document as any;
global.navigator = window.navigator;
global.location = window.location;
global.HTMLElement = window.HTMLElement;
global.Element = window.Element;

// Mock functions for Next.js router
const mockPush = () => {};
const mockReplace = () => {};
const mockPrefetch = () => Promise.resolve();
const mockBack = () => {};
const mockForward = () => {};
const mockRefresh = () => {};

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8001';

// Global test utilities
global.console = {
  ...console,
  // Suppress console.log in tests unless explicitly needed
  log: () => {},
  // Keep error and warn for debugging
  error: console.error,
  warn: console.warn,
  info: console.info,
  debug: console.debug,
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Clean up DOM after each test
afterEach(() => {
  document.body.innerHTML = '';
});

// Export mocks for use in tests
export const mockRouter = {
  push: mockPush,
  replace: mockReplace,
  prefetch: mockPrefetch,
  back: mockBack,
};