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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useSalesSummary } from '@/hooks/useReports';
import { formatCurrency, formatDate, formatPercentage } from '@/lib/formatters';
import { format, startOfMonth, endOfMonth, subMonths, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns';

type PeriodType = 'current_month' | 'last_month' | 'current_quarter' | 'current_year' | 'custom';

export const SalesSummaryPage = () => {
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

  const { data: report, isLoading } = useSalesSummary(dateRange.startDate, dateRange.endDate);

  // Find top performers
  const topCustomer = report?.by_customer[0];
  const topItem = report?.by_item[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/reports')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">Sales Summary</h1>
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
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : report ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Total Sales</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{formatCurrency(report.total_sales)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Customer</CardTitle>
              </CardHeader>
              <CardContent>
                {topCustomer ? (
                  <div>
                    <div className="text-xl font-bold truncate">{topCustomer.customer_name}</div>
                    <div className="flex items-center gap-2 mt-2">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-muted-foreground">
                        {formatCurrency(topCustomer.total_sales)}
                      </span>
                      <Badge variant="secondary">
                        {formatPercentage(topCustomer.percentage_of_total)}
                      </Badge>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No sales data</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Item</CardTitle>
              </CardHeader>
              <CardContent>
                {topItem ? (
                  <div>
                    <div className="text-xl font-bold truncate">{topItem.item_name}</div>
                    <div className="flex items-center gap-2 mt-2">
                      <TrendingUp className="h-4 w-4 text-blue-600" />
                      <span className="text-sm text-muted-foreground">
                        {formatCurrency(topItem.total_sales)}
                      </span>
                      <Badge variant="secondary">
                        {topItem.quantity_sold} sold
                      </Badge>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No sales data</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Tabbed Views */}
          <Card>
            <CardHeader>
              <CardTitle>Sales Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="customer" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="customer">By Customer</TabsTrigger>
                  <TabsTrigger value="item">By Item</TabsTrigger>
                </TabsList>

                {/* By Customer Tab */}
                <TabsContent value="customer" className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Customer</TableHead>
                        <TableHead className="text-right">Invoice Count</TableHead>
                        <TableHead className="text-right">Total Sales</TableHead>
                        <TableHead className="text-right">Percentage</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.by_customer.length > 0 ? (
                        <>
                          {report.by_customer.map((customer, index) => (
                            <TableRow key={customer.customer_id}>
                              <TableCell className="font-medium">
                                {customer.customer_name}
                                {index === 0 && (
                                  <Badge variant="outline" className="ml-2">Top</Badge>
                                )}
                              </TableCell>
                              <TableCell className="text-right">
                                {customer.invoice_count}
                              </TableCell>
                              <TableCell className="text-right font-semibold">
                                {formatCurrency(customer.total_sales)}
                              </TableCell>
                              <TableCell className="text-right">
                                <Badge variant="secondary">
                                  {formatPercentage(customer.percentage_of_total)}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                          <TableRow className="font-bold border-t-2">
                            <TableCell>Total</TableCell>
                            <TableCell className="text-right">
                              {report.by_customer.reduce((sum, c) => sum + c.invoice_count, 0)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(report.total_sales)}
                            </TableCell>
                            <TableCell className="text-right">100%</TableCell>
                          </TableRow>
                        </>
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                            No customer sales data available
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TabsContent>

                {/* By Item Tab */}
                <TabsContent value="item" className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead className="text-right">Quantity Sold</TableHead>
                        <TableHead className="text-right">Total Sales</TableHead>
                        <TableHead className="text-right">Percentage</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.by_item.length > 0 ? (
                        <>
                          {report.by_item.map((item, index) => (
                            <TableRow key={item.item_id}>
                              <TableCell className="font-medium">
                                {item.item_name}
                                {index === 0 && (
                                  <Badge variant="outline" className="ml-2">Top</Badge>
                                )}
                              </TableCell>
                              <TableCell className="text-right">
                                {item.quantity_sold}
                              </TableCell>
                              <TableCell className="text-right font-semibold">
                                {formatCurrency(item.total_sales)}
                              </TableCell>
                              <TableCell className="text-right">
                                <Badge variant="secondary">
                                  {formatPercentage(item.percentage_of_total)}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                          <TableRow className="font-bold border-t-2">
                            <TableCell>Total</TableCell>
                            <TableCell className="text-right">
                              {report.by_item.reduce((sum, i) => sum + i.quantity_sold, 0)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(report.total_sales)}
                            </TableCell>
                            <TableCell className="text-right">100%</TableCell>
                          </TableRow>
                        </>
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                            No item sales data available
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No sales data available for the selected period</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
