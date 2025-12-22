import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings } from 'lucide-react';

export const OnboardingSettingsPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Configure onboarding portal preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Onboarding Settings</CardTitle>
          <CardDescription>Manage your onboarding portal configuration</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Settings className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <h3 className="mb-2 text-lg font-semibold">Coming Soon</h3>
          <p className="text-sm text-muted-foreground">
            Settings configuration will be available in a future update
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
