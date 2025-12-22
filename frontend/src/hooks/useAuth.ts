import { useAuthStore } from '@/stores/authStore';

export const useAuth = () => {
  const {
    user,
    isLoading,
    isAuthenticated,
    mustChangePassword,
    login,
    logout,
    changePassword,
    checkAuth,
  } = useAuthStore();

  return {
    user,
    isLoading,
    isAuthenticated,
    mustChangePassword,
    login,
    logout,
    changePassword,
    checkAuth,
  };
};
