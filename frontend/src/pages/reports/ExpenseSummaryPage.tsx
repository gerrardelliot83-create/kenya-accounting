import { useState, useMemo } from 'react';
import { ArrowLeft, Download, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useExpenseSummaryReport } from '@/hooks/useReports';
import { formatCurrency, formatDate, formatPercentage } from '@/lib/formatters';
import { format, startOfMonth, endOfMonth, subMonths, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

type PeriodType = 'current_month' | 'last_month' | 'current_quarter' | 'current_year' | 'custom';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

export const ExpenseSummaryPage = () => {
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

  const { data: report, isLoading } = useExpenseSummaryReport(dateRange.startDate, dateRange.endDate);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!report) return [];
    return report.categories.map((cat) => ({
      name: cat.category,
      value: cat.total,
    }));
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
            <h1 className="text-3xl font-semibold">Expense Summary</h1>
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
            Export CSV
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
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Total Expenses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-4">
                <div className="text-4xl font-bold">{formatCurrency(report.total_expenses)}</div>
                {report.largest_category && (
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      Largest: <span className="font-medium">{report.largest_category}</span>
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Chart and Table */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Expense Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Category List */}
            <Card>
              <CardHeader>
                <CardTitle>Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {report.categories.map((category, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <div>
                          <p className="font-medium">{category.category}</p>
                          <p className="text-sm text-muted-foreground">
                            {category.count} transaction{category.count !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{formatCurrency(category.total)}</p>
                        <Badge variant="secondary" className="mt-1">
                          {formatPercentage(category.percentage)}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Count</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Percentage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.categories.map((category, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                          />
                          {category.category}
                          {category.category === report.largest_category && (
                            <Badge variant="outline" className="ml-2">Highest</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{category.count}</TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(category.total)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatPercentage(category.percentage)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-bold border-t-2">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">
                      {report.categories.reduce((sum, cat) => sum + cat.count, 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(report.total_expenses)}
                    </TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No expense data available for the selected period</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
