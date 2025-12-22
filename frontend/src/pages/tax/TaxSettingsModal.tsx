import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useUpdateTaxSettings } from '@/hooks/useTax';
import type { TaxSettings, UpdateTaxSettingsRequest } from '@/types/tax';

interface TaxSettingsModalProps {
  open: boolean;
  onClose: () => void;
  settings?: TaxSettings;
}

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
];

export const TaxSettingsModal = ({ open, onClose, settings }: TaxSettingsModalProps) => {
  const { register, handleSubmit, watch, setValue, reset } = useForm<UpdateTaxSettingsRequest>({
    defaultValues: {
      is_vat_registered: settings?.is_vat_registered || false,
      vat_registration_number: settings?.vat_registration_number || '',
      vat_registration_date: settings?.vat_registration_date || '',
      is_tot_eligible: settings?.is_tot_eligible || false,
      financial_year_start_month: settings?.financial_year_start_month || 1,
    },
  });

  const updateSettings = useUpdateTaxSettings();
  const isVATRegistered = watch('is_vat_registered');

  useEffect(() => {
    if (settings) {
      reset({
        is_vat_registered: settings.is_vat_registered,
        vat_registration_number: settings.vat_registration_number || '',
        vat_registration_date: settings.vat_registration_date || '',
        is_tot_eligible: settings.is_tot_eligible,
        financial_year_start_month: settings.financial_year_start_month,
      });
    }
  }, [settings, reset]);

  const onSubmit = async (data: UpdateTaxSettingsRequest) => {
    await updateSettings.mutateAsync(data);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Tax Settings</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-4">
            {/* VAT Registration */}
            <div className="space-y-4 rounded-lg border p-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_vat_registered"
                  checked={isVATRegistered}
                  onCheckedChange={(checked) => setValue('is_vat_registered', checked as boolean)}
                />
                <Label htmlFor="is_vat_registered" className="font-medium">
                  VAT Registered Business
                </Label>
              </div>

              {isVATRegistered && (
                <div className="space-y-4 pl-6">
                  <div className="space-y-2">
                    <Label htmlFor="vat_registration_number">VAT Registration Number</Label>
                    <Input
                      id="vat_registration_number"
                      {...register('vat_registration_number')}
                      placeholder="e.g., P051234567X"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="vat_registration_date">VAT Registration Date</Label>
                    <Input
                      id="vat_registration_date"
                      type="date"
                      {...register('vat_registration_date')}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* TOT Eligibility */}
            <div className="space-y-2 rounded-lg border p-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_tot_eligible"
                  {...register('is_tot_eligible')}
                  onCheckedChange={(checked) => setValue('is_tot_eligible', checked as boolean)}
                />
                <div>
                  <Label htmlFor="is_tot_eligible" className="font-medium">
                    Eligible for Turnover Tax (TOT)
                  </Label>
                  <p className="text-xs text-muted-foreground mt-1">
                    For businesses with annual turnover below KES 25M
                  </p>
                </div>
              </div>
            </div>

            {/* Financial Year Start */}
            <div className="space-y-2">
              <Label htmlFor="financial_year_start_month">Financial Year Start Month</Label>
              <Select
                value={watch('financial_year_start_month')?.toString()}
                onValueChange={(value) => setValue('financial_year_start_month', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select month" />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map((month) => (
                    <SelectItem key={month.value} value={month.value.toString()}>
                      {month.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateSettings.isPending}>
              {updateSettings.isPending ? 'Saving...' : 'Save Settings'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
