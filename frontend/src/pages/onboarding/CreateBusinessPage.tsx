import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateApplication, useSubmitApplication } from '@/hooks/useOnboarding';
import {
  KENYAN_COUNTIES,
  BUSINESS_TYPES,
} from '@/lib/kenya-constants';
import {
  validateKraPin,
  validateKenyanPhone,
  validateKenyanId,
} from '@/lib/kenya-validation';
import { ArrowLeft, Save, Send } from 'lucide-react';

// Validation schema
const applicationSchema = z.object({
  business_name: z.string().min(2, 'Business name must be at least 2 characters'),
  business_type: z.enum(['sole_proprietor', 'partnership', 'limited_company']),
  kra_pin: z.string().refine(validateKraPin, {
    message: 'Invalid KRA PIN format. Expected: A123456789Z',
  }),
  county: z.string().min(1, 'County is required'),
  sub_county: z.string().optional(),
  phone: z.string().refine(validateKenyanPhone, {
    message: 'Invalid phone number. Expected: +254XXXXXXXXX or 07XXXXXXXX',
  }),
  email: z.string().email('Invalid email address'),
  owner_name: z.string().min(2, 'Owner name must be at least 2 characters'),
  owner_national_id: z.string().refine(validateKenyanId, {
    message: 'Invalid National ID format. Expected: 8 digits',
  }),
  owner_phone: z.string().refine(validateKenyanPhone, {
    message: 'Invalid phone number. Expected: +254XXXXXXXXX or 07XXXXXXXX',
  }),
  owner_email: z.string().email('Invalid email address'),
  vat_registered: z.boolean(),
  tot_registered: z.boolean(),
});

type ApplicationFormData = z.infer<typeof applicationSchema>;

export const CreateBusinessPage = () => {
  const navigate = useNavigate();
  const [saveAsDraft, setSaveAsDraft] = useState(false);

  const createMutation = useCreateApplication();
  const submitMutation = useSubmitApplication();

  const form = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
    defaultValues: {
      business_name: '',
      business_type: 'sole_proprietor',
      kra_pin: '',
      county: '',
      sub_county: '',
      phone: '',
      email: '',
      owner_name: '',
      owner_national_id: '',
      owner_phone: '',
      owner_email: '',
      vat_registered: false,
      tot_registered: false,
    },
  });

  const handleSubmit = async (data: ApplicationFormData) => {
    try {
      // First create the application
      const createdApp = await createMutation.mutateAsync(data);

      // If not saving as draft, submit it
      if (!saveAsDraft && createdApp.id) {
        await submitMutation.mutateAsync(createdApp.id);
      }

      navigate('/onboarding');
    } catch (error) {
      // Errors are handled by the mutations
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Create New Application</h1>
          <p className="mt-2 text-muted-foreground">
            Submit a new business onboarding application
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/onboarding')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Cancel
        </Button>
      </div>

      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Business Information */}
        <Card>
          <CardHeader>
            <CardTitle>Business Information</CardTitle>
            <CardDescription>Basic information about the business</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="business_name">Business Name *</Label>
              <Input
                id="business_name"
                placeholder="Enter business name"
                {...form.register('business_name')}
              />
              {form.formState.errors.business_name && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.business_name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="business_type">Business Type *</Label>
              <Select
                value={form.watch('business_type')}
                onValueChange={(value) =>
                  form.setValue('business_type', value as any)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {BUSINESS_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="kra_pin">KRA PIN *</Label>
              <Input
                id="kra_pin"
                placeholder="A123456789Z"
                {...form.register('kra_pin')}
                className="uppercase"
              />
              {form.formState.errors.kra_pin && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.kra_pin.message}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Format: Letter + 9 digits + Letter (e.g., A123456789Z)
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="county">County *</Label>
                <Select
                  value={form.watch('county')}
                  onValueChange={(value) => form.setValue('county', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select county" />
                  </SelectTrigger>
                  <SelectContent>
                    {KENYAN_COUNTIES.map((county) => (
                      <SelectItem key={county} value={county}>
                        {county}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {form.formState.errors.county && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.county.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="sub_county">Sub County</Label>
                <Input
                  id="sub_county"
                  placeholder="Enter sub county"
                  {...form.register('sub_county')}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="phone">Business Phone *</Label>
                <Input
                  id="phone"
                  placeholder="+254712345678"
                  {...form.register('phone')}
                />
                {form.formState.errors.phone && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.phone.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Business Email *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="business@example.com"
                  {...form.register('email')}
                />
                {form.formState.errors.email && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="vat_registered"
                  checked={form.watch('vat_registered')}
                  onCheckedChange={(checked) =>
                    form.setValue('vat_registered', checked === true)
                  }
                />
                <Label htmlFor="vat_registered" className="font-normal">
                  VAT Registered
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="tot_registered"
                  checked={form.watch('tot_registered')}
                  onCheckedChange={(checked) =>
                    form.setValue('tot_registered', checked === true)
                  }
                />
                <Label htmlFor="tot_registered" className="font-normal">
                  TOT Registered
                </Label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Owner Information */}
        <Card>
          <CardHeader>
            <CardTitle>Owner Information</CardTitle>
            <CardDescription>Details about the business owner</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="owner_name">Full Name *</Label>
              <Input
                id="owner_name"
                placeholder="John Doe"
                {...form.register('owner_name')}
              />
              {form.formState.errors.owner_name && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.owner_name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="owner_national_id">National ID *</Label>
              <Input
                id="owner_national_id"
                placeholder="12345678"
                {...form.register('owner_national_id')}
              />
              {form.formState.errors.owner_national_id && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.owner_national_id.message}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Format: 8 digits (e.g., 12345678)
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="owner_phone">Phone *</Label>
                <Input
                  id="owner_phone"
                  placeholder="+254712345678"
                  {...form.register('owner_phone')}
                />
                {form.formState.errors.owner_phone && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.owner_phone.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="owner_email">Email *</Label>
                <Input
                  id="owner_email"
                  type="email"
                  placeholder="owner@example.com"
                  {...form.register('owner_email')}
                />
                {form.formState.errors.owner_email && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.owner_email.message}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-3">
          <Button
            type="submit"
            variant="outline"
            onClick={() => setSaveAsDraft(true)}
            disabled={createMutation.isPending || submitMutation.isPending}
          >
            <Save className="mr-2 h-4 w-4" />
            Save as Draft
          </Button>
          <Button
            type="submit"
            onClick={() => setSaveAsDraft(false)}
            disabled={createMutation.isPending || submitMutation.isPending}
          >
            <Send className="mr-2 h-4 w-4" />
            {createMutation.isPending || submitMutation.isPending
              ? 'Submitting...'
              : 'Create & Submit'}
          </Button>
        </div>
      </form>
    </div>
  );
};
