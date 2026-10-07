import { TelegramUser, TelegramWebApp } from "@/types/telegram";

/**
 * Safely retrieves the Telegram WebApp object if running inside Telegram Mini App.
 * Returns null if running in standard desktop/mobile browser.
 */
export function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.Telegram?.WebApp ?? null;
}

/**
 * Checks whether the current session is executing inside a Telegram Mini App host.
 */
export function isTelegramWebAppAvailable(): boolean {
  return getTelegramWebApp() !== null;
}

/**
 * Safely extracts raw initData query string for backend verification.
 */
export function getTelegramInitData(): string {
  const tg = getTelegramWebApp();
  return tg?.initData ?? "";
}

/**
 * Retrieves client-side user metadata if available.
 * NOTE: For trusted authentication, backend HMAC verification of initData MUST be used.
 */
export function getTelegramUser(): TelegramUser | null {
  const tg = getTelegramWebApp();
  return tg?.initDataUnsafe?.user ?? null;
}

/**
 * Initializes the Telegram Mini App viewport:
 * Expands to full height and notifies the client that the UI is ready.
 */
export function initTelegramWebApp(): void {
  const tg = getTelegramWebApp();
  if (tg) {
    try {
      tg.ready();
      tg.expand();
    } catch (e) {
      console.warn("Telegram WebApp initialization error:", e);
    }
  }
}
