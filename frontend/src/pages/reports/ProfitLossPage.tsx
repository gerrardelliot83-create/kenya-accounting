import { useState, useMemo } from 'react';
import { ArrowLeft, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useProfitLoss } from '@/hooks/useReports';
import { formatCurrency, formatDate, formatPercentage } from '@/lib/formatters';
import { format, startOfMonth, endOfMonth, subMonths, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

type PeriodType = 'current_month' | 'last_month' | 'current_quarter' | 'current_year' | 'custom';

export const ProfitLossPage = () => {
  const navigate = useNavigate();
  const [periodType, setPeriodType] = useState<PeriodType>('current_month');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

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
      case 'current_year':
        start = startOfYear(today);
        end = endOfYear(today);
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

  const { data: report, isLoading } = useProfitLoss(dateRange.startDate, dateRange.endDate);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!report) return [];
    return [
      {
        name: 'Overview',
        Revenue: report.total_revenue,
        Expenses: report.total_expenses,
        Profit: report.net_profit,
      },
    ];
  }, [report]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/reports')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">Profit & Loss Statement</h1>
            {dateRange.startDate && dateRange.endDate && (
              <p className="mt-1 text-muted-foreground">
                {formatDate(dateRange.startDate)} - {formatDate(dateRange.endDate)}
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export PDF
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Period Selector */}
      <Card>
        <CardContent className="pt-6">
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
                  <SelectItem value="current_year">Current Year</SelectItem>
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
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : report ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(report.total_revenue)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Expenses
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(report.total_expenses)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Gross Profit
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(report.gross_profit)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Net Profit
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${report.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(report.net_profit)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Margin: {formatPercentage(report.profit_margin)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue vs Expenses</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  <Legend />
                  <Bar dataKey="Revenue" fill="#10b981" />
                  <Bar dataKey="Expenses" fill="#f59e0b" />
                  <Bar dataKey="Profit" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Detailed Statement */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Statement</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Revenue Section */}
              <div>
                <div className="flex justify-between items-center py-3 border-b-2 border-primary">
                  <h3 className="text-lg font-semibold">Revenue</h3>
                  <span className="text-lg font-bold">{formatCurrency(report.total_revenue)}</span>
                </div>
              </div>

              {/* Expenses Section */}
              <div>
                <div className="flex justify-between items-center py-3 border-b-2 border-primary">
                  <h3 className="text-lg font-semibold">Expenses</h3>
                  <span className="text-lg font-bold">{formatCurrency(report.total_expenses)}</span>
                </div>
                <div className="mt-4 space-y-2">
                  {report.expenses_by_category.map((category, index) => (
                    <div key={index} className="flex justify-between items-center py-2 px-4 bg-muted/50 rounded">
                      <div className="flex-1">
                        <span className="font-medium">{category.category}</span>
                        <span className="ml-2 text-sm text-muted-foreground">
                          ({formatPercentage(category.percentage)})
                        </span>
                      </div>
                      <span className="font-semibold">{formatCurrency(category.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Profit Calculations */}
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2">
                  <span className="font-medium">Gross Profit</span>
                  <span className="font-bold">{formatCurrency(report.gross_profit)}</span>
                </div>
                <div className="flex justify-between items-center py-3 border-t-2 border-primary">
                  <span className="text-lg font-semibold">Net Profit</span>
                  <span className={`text-lg font-bold ${report.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(report.net_profit)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 bg-muted/50 rounded px-4">
                  <span className="font-medium">Profit Margin</span>
                  <span className="font-bold">{formatPercentage(report.profit_margin)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No data available for the selected period</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
