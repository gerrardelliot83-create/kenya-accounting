import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Check, X } from 'lucide-react';

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number')
      .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

const PasswordRequirement = ({ met, text }: { met: boolean; text: string }) => (
  <div className="flex items-center gap-2 text-sm">
    {met ? (
      <Check className="h-4 w-4 text-green-600" />
    ) : (
      <X className="h-4 w-4 text-muted-foreground" />
    )}
    <span className={met ? 'text-green-600' : 'text-muted-foreground'}>{text}</span>
  </div>
);

export const ChangePasswordPage = () => {
  const navigate = useNavigate();
  const { changePassword } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const newPassword = watch('newPassword', '');

  const passwordRequirements = {
    minLength: newPassword.length >= 8,
    hasUppercase: /[A-Z]/.test(newPassword),
    hasLowercase: /[a-z]/.test(newPassword),
    hasNumber: /[0-9]/.test(newPassword),
    hasSpecial: /[^A-Za-z0-9]/.test(newPassword),
  };

  const onSubmit = async (data: PasswordFormData) => {
    try {
      setIsLoading(true);
      setError(null);
      await changePassword({
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
      });
      navigate('/dashboard');
    } catch (err) {
      setError(
        err && typeof err === 'object' && 'message' in err
          ? (err.message as string)
          : 'Failed to change password. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-semibold">Change Password</CardTitle>
          <CardDescription>
            You must change your password before continuing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">Current Password</Label>
              <Input
                id="currentPassword"
                type="password"
                {...register('currentPassword')}
                disabled={isLoading}
                aria-invalid={errors.currentPassword ? 'true' : 'false'}
              />
              {errors.currentPassword && (
                <p className="text-sm text-destructive" role="alert">
                  {errors.currentPassword.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">New Password</Label>
              <Input
                id="newPassword"
                type="password"
                {...register('newPassword')}
                disabled={isLoading}
                aria-invalid={errors.newPassword ? 'true' : 'false'}
              />
              {errors.newPassword && (
                <p className="text-sm text-destructive" role="alert">
                  {errors.newPassword.message}
                </p>
              )}

              <div className="space-y-2 rounded-md border p-3">
                <p className="text-sm font-medium">Password Requirements:</p>
                <PasswordRequirement
                  met={passwordRequirements.minLength}
                  text="At least 8 characters"
                />
                <PasswordRequirement
                  met={passwordRequirements.hasUppercase}
                  text="One uppercase letter"
                />
                <PasswordRequirement
                  met={passwordRequirements.hasLowercase}
                  text="One lowercase letter"
                />
                <PasswordRequirement met={passwordRequirements.hasNumber} text="One number" />
                <PasswordRequirement
                  met={passwordRequirements.hasSpecial}
                  text="One special character"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm New Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                {...register('confirmPassword')}
                disabled={isLoading}
                aria-invalid={errors.confirmPassword ? 'true' : 'false'}
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive" role="alert">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <LoadingSpinner size="sm" className="border-primary-foreground border-t-transparent" />
                  Changing Password...
                </span>
              ) : (
                'Change Password'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
