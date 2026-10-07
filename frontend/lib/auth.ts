import { api } from "@/lib/api";
import { getTelegramInitData, isTelegramWebAppAvailable } from "@/lib/telegram";
import { User } from "@/types/user";

export class AuthService {
  /**
   * Attempts to authenticate the student via Telegram WebApp initData.
   */
  async authenticateWithTelegram(): Promise<User> {
    const initData = getTelegramInitData();
    if (!initData) {
      throw new Error("Telegram initData is empty or unavailable.");
    }
    const response = await api.loginTelegram(initData);
    return response.user;
  }

  /**
   * Development login for desktop browser testing.
   */
  async authenticateDev(firstName = "Dev Student"): Promise<User> {
    const response = await api.loginDev({
      telegram_id: 12345678,
      first_name: firstName,
      username: "dev_student",
    });
    return response.user;
  }

  /**
   * Fetches the profile of the currently authenticated student.
   */
  async getCurrentUser(): Promise<User | null> {
    const token = api.getToken();
    if (!token) return null;
    try {
      return await api.getMe();
    } catch {
      api.clearToken();
      return null;
    }
  }

  /**
   * Clears session and logs out student.
   */
  logout(): void {
    api.clearToken();
  }

  /**
   * Checks if an authentication token is present in storage.
   */
  hasToken(): boolean {
    return !!api.getToken();
  }
}

export const authService = new AuthService();
