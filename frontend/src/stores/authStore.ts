import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';
import type { User, LoginRequest, ChangePasswordRequest } from '@/types/auth';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  mustChangePassword: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mustChangePassword: false,

      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true });
          const response = await apiClient.login(credentials);

          set({
            user: response.user,
            isAuthenticated: true,
            mustChangePassword: response.user.mustChangePassword,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        try {
          await apiClient.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            mustChangePassword: false,
          });
        }
      },

      changePassword: async (data: ChangePasswordRequest) => {
        try {
          set({ isLoading: true });
          await apiClient.changePassword(data);

          // Update user state to clear mustChangePassword flag
          const currentUser = get().user;
          if (currentUser) {
            set({
              user: { ...currentUser, mustChangePassword: false },
              mustChangePassword: false,
              isLoading: false,
            });
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      checkAuth: async () => {
        try {
          set({ isLoading: true });
          const user = await apiClient.getCurrentUser();

          set({
            user,
            isAuthenticated: true,
            mustChangePassword: user.mustChangePassword,
            isLoading: false,
          });
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            mustChangePassword: false,
            isLoading: false,
          });
        }
      },

      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
          mustChangePassword: user?.mustChangePassword || false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        mustChangePassword: state.mustChangePassword,
      }),
    }
  )
);
