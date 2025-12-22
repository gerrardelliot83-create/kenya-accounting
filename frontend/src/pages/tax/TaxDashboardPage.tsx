import { useState, useMemo } from 'react';
import { Settings, Download, Calendar, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTaxSettings, useVATSummary, useTOTSummary, useFilingGuidance, useExportVATReturn } from '@/hooks/useTax';
import { TaxSettingsModal } from './TaxSettingsModal';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { format, startOfMonth, endOfMonth, subMonths, startOfQuarter, endOfQuarter } from 'date-fns';

type PeriodType = 'current_month' | 'last_month' | 'current_quarter' | 'custom';

export const TaxDashboardPage = () => {
  const [periodType, setPeriodType] = useState<PeriodType>('current_month');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const { data: settings, isLoading: settingsLoading } = useTaxSettings();
  const { data: filingGuidance } = useFilingGuidance();
  const exportVATReturn = useExportVATReturn();

  // Calculate date range based on period type
  const dateRange = useMemo(() => {
    const today = new Date();
    let start: Date;
    let end: Date;

    switch (periodType) {
      case 'current_month':
        start = startOfMonth(today);
        end = endOfMonth(today);
        break;
      case 'last_month':
        start = startOfMonth(subMonths(today, 1));
        end = endOfMonth(subMonths(today, 1));
        break;
      case 'current_quarter':
        start = startOfQuarter(today);
        end = endOfQuarter(today);
        break;
      case 'custom':
        if (!customStartDate || !customEndDate) {
          return { startDate: '', endDate: '' };
        }
        return { startDate: customStartDate, endDate: customEndDate };
      default:
        start = startOfMonth(today);
        end = endOfMonth(today);
    }

    return {
      startDate: format(start, 'yyyy-MM-dd'),
      endDate: format(end, 'yyyy-MM-dd'),
    };
  }, [periodType, customStartDate, customEndDate]);

  const { data: vatSummary, isLoading: vatLoading } = useVATSummary(
    dateRange.startDate,
    dateRange.endDate
  );

  const { data: totSummary, isLoading: totLoading } = useTOTSummary(
    dateRange.startDate,
    dateRange.endDate
  );

  const handleExportVATReturn = () => {
    if (dateRange.startDate && dateRange.endDate) {
      exportVATReturn.mutate({ startDate: dateRange.startDate, endDate: dateRange.endDate });
    }
  };

  const calculateDaysUntilFiling = (filingDate: string) => {
    const today = new Date();
    const filing = new Date(filingDate);
    const diffTime = filing.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Tax Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your VAT and TOT compliance
          </p>
        </div>
        <Button onClick={() => setIsSettingsOpen(true)} variant="outline">
          <Settings className="mr-2 h-4 w-4" />
          Tax Settings
        </Button>
      </div>

      {/* Tax Status Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">VAT Registration</CardTitle>
          </CardHeader>
          <CardContent>
            {settingsLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : settings?.is_vat_registered ? (
              <div className="space-y-2">
                <Badge className="bg-green-500">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Registered
                </Badge>
                {settings.vat_registration_number && (
                  <p className="text-sm text-muted-foreground">
                    PIN: {settings.vat_registration_number}
                  </p>
                )}
              </div>
            ) : (
              <Badge variant="secondary">Not Registered</Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Turnover Tax (TOT)</CardTitle>
          </CardHeader>
          <CardContent>
            {settingsLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : settings?.is_tot_eligible ? (
              <Badge className="bg-blue-500">
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Eligible
              </Badge>
            ) : (
              <Badge variant="secondary">Not Eligible</Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Period Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select Period</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 md:flex-row md:items-end">
            <div className="flex-1 space-y-2">
              <Label>Period</Label>
              <Select value={periodType} onValueChange={(value) => setPeriodType(value as PeriodType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="current_month">Current Month</SelectItem>
                  <SelectItem value="last_month">Last Month</SelectItem>
                  <SelectItem value="current_quarter">Current Quarter</SelectItem>
                  <SelectItem value="custom">Custom Range</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {periodType === 'custom' && (
              <>
                <div className="flex-1 space-y-2">
                  <Label>Start Date</Label>
                  <Input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                  />
                </div>
                <div className="flex-1 space-y-2">
                  <Label>End Date</Label>
                  <Input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                  />
                </div>
              </>
            )}

            {periodType !== 'custom' && dateRange.startDate && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                {formatDate(dateRange.startDate)} - {formatDate(dateRange.endDate)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* VAT Summary */}
      {settings?.is_vat_registered && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>VAT Summary</CardTitle>
                <CardDescription>
                  {dateRange.startDate && dateRange.endDate && (
                    <>Period: {formatDate(dateRange.startDate)} - {formatDate(dateRange.endDate)}</>
                  )}
                </CardDescription>
              </div>
              <Button
                onClick={handleExportVATReturn}
                disabled={!dateRange.startDate || !dateRange.endDate || exportVATReturn.isPending}
                size="sm"
              >
                <Download className="mr-2 h-4 w-4" />
                Export iTax CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {vatLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : vatSummary ? (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Output VAT (Sales)</p>
                    <p className="text-2xl font-bold">{formatCurrency(vatSummary.output_vat)}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Input VAT (Expenses)</p>
                    <p className="text-2xl font-bold">{formatCurrency(vatSummary.input_vat)}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Net VAT</p>
                    <p className={`text-2xl font-bold ${vatSummary.net_vat >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(Math.abs(vatSummary.net_vat))}
                    </p>
                  </div>
                </div>

                <Alert variant={vatSummary.net_vat >= 0 ? 'default' : 'default'}>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {vatSummary.net_vat >= 0
                      ? `You owe KRA ${formatCurrency(vatSummary.net_vat)}`
                      : `KRA owes you ${formatCurrency(Math.abs(vatSummary.net_vat))}`}
                  </AlertDescription>
                </Alert>

                <div className="grid gap-4 md:grid-cols-2 pt-4 border-t">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Total Sales</p>
                    <p className="text-lg font-semibold">{formatCurrency(vatSummary.total_sales)}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Total Expenses with VAT</p>
                    <p className="text-lg font-semibold">{formatCurrency(vatSummary.total_expenses_with_vat)}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No VAT data available for this period</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* TOT Summary */}
      {settings?.is_tot_eligible && (
        <Card>
          <CardHeader>
            <CardTitle>TOT Summary</CardTitle>
            <CardDescription>
              {dateRange.startDate && dateRange.endDate && (
                <>Period: {formatDate(dateRange.startDate)} - {formatDate(dateRange.endDate)}</>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {totLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : totSummary ? (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Gross Turnover</p>
                    <p className="text-2xl font-bold">{formatCurrency(totSummary.gross_turnover)}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">TOT Payable ({totSummary.tot_rate}%)</p>
                    <p className="text-2xl font-bold text-red-600">{formatCurrency(totSummary.tot_payable)}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No TOT data available for this period</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filing Guidance */}
      {filingGuidance && filingGuidance.tax_type !== 'none' && (
        <Card>
          <CardHeader>
            <CardTitle>Filing Guidance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm font-medium">Next Filing Deadline</p>
                <p className="text-2xl font-bold mt-1">{formatDate(filingGuidance.next_filing_date)}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {calculateDaysUntilFiling(filingGuidance.next_filing_date)} days remaining
                </p>
              </div>
              <Badge variant="outline" className="text-lg px-4 py-2">
                {filingGuidance.tax_type.toUpperCase()}
              </Badge>
            </div>

            <div>
              <p className="font-medium mb-2">Filing Frequency</p>
              <p className="text-sm text-muted-foreground">{filingGuidance.filing_frequency}</p>
            </div>

            {filingGuidance.requirements.length > 0 && (
              <div>
                <p className="font-medium mb-2">Requirements</p>
                <ul className="space-y-1">
                  {filingGuidance.requirements.map((req, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600" />
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {filingGuidance.helpful_notes.length > 0 && (
              <div>
                <p className="font-medium mb-2">Helpful Notes</p>
                <ul className="space-y-1">
                  {filingGuidance.helpful_notes.map((note, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <AlertCircle className="h-4 w-4 mt-0.5" />
                      <span>{note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tax Settings Modal */}
      <TaxSettingsModal
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
      />
    </div>
  );
};
