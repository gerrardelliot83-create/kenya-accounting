export type UserRole =
  | 'business_admin'
  | 'bookkeeper'
  | 'onboarding_agent'
  | 'support_agent'
  | 'system_admin';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  businessId?: string;
  mustChangePassword: boolean;
  firstName?: string;
  lastName?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  mustChangePassword: boolean;
}
