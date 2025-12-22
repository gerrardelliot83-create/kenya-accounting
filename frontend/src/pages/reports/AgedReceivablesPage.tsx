import { useState } from 'react';
import { ArrowLeft, Download, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { useAgedReceivables } from '@/hooks/useReports';
import { formatCurrency, formatDate, formatPercentage } from '@/lib/formatters';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const AgedReceivablesPage = () => {
  const navigate = useNavigate();
  const [asOfDate, setAsOfDate] = useState(format(new Date(), 'yyyy-MM-dd'));

  const { data: report, isLoading } = useAgedReceivables(asOfDate);

  // Prepare chart data
  const chartData = report?.buckets.map((bucket) => ({
    name: bucket.label,
    amount: bucket.total_amount,
    count: bucket.invoice_count,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/reports')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">Aged Receivables</h1>
            <p className="mt-1 text-muted-foreground">
              Outstanding invoices and aging analysis
            </p>
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

      {/* Date Selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4">
            <div className="flex-1 space-y-2 max-w-xs">
              <Label>As of Date</Label>
              <Input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
              />
            </div>
            {report && (
              <div className="text-sm text-muted-foreground">
                Report generated as of {formatDate(report.as_of_date)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : report ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Total Outstanding</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{formatCurrency(report.total_outstanding)}</div>
                <p className="text-sm text-muted-foreground mt-2">
                  Across {report.buckets.reduce((sum, b) => sum + b.invoice_count, 0)} invoices
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Overdue Percentage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-4xl font-bold ${report.overdue_percentage > 30 ? 'text-red-600' : report.overdue_percentage > 15 ? 'text-orange-600' : 'text-green-600'}`}>
                  {formatPercentage(report.overdue_percentage)}
                </div>
                {report.overdue_percentage > 30 && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      High overdue percentage. Consider following up on outstanding invoices.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Aging Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Aging Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  <Legend />
                  <Bar dataKey="amount" fill="#3b82f6" name="Amount" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Aging Buckets Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Aging Buckets</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Age Range</TableHead>
                    <TableHead className="text-right">Invoice Count</TableHead>
                    <TableHead className="text-right">Total Amount</TableHead>
                    <TableHead className="text-right">Percentage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.buckets.map((bucket, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{bucket.label}</TableCell>
                      <TableCell className="text-right">{bucket.invoice_count}</TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(bucket.total_amount)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="secondary">
                          {formatPercentage((bucket.total_amount / report.total_outstanding) * 100)}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-bold border-t-2">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">
                      {report.buckets.reduce((sum, b) => sum + b.invoice_count, 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(report.total_outstanding)}
                    </TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Detailed Invoice List */}
          <Card>
            <CardHeader>
              <CardTitle>Invoice Details</CardTitle>
              <CardDescription>Click to expand each aging bucket</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {report.buckets.map((bucket, bucketIndex) => (
                  <AccordionItem key={bucketIndex} value={`bucket-${bucketIndex}`}>
                    <AccordionTrigger>
                      <div className="flex items-center justify-between w-full pr-4">
                        <span className="font-medium">{bucket.label}</span>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-muted-foreground">
                            {bucket.invoice_count} invoice{bucket.invoice_count !== 1 ? 's' : ''}
                          </span>
                          <span className="font-semibold">
                            {formatCurrency(bucket.total_amount)}
                          </span>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      {bucket.invoices && bucket.invoices.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Invoice #</TableHead>
                              <TableHead>Customer</TableHead>
                              <TableHead>Due Date</TableHead>
                              <TableHead className="text-right">Days Overdue</TableHead>
                              <TableHead className="text-right">Amount</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {bucket.invoices.map((invoice) => (
                              <TableRow key={invoice.invoice_id}>
                                <TableCell className="font-medium">
                                  {invoice.invoice_number}
                                </TableCell>
                                <TableCell>{invoice.customer_name}</TableCell>
                                <TableCell>{formatDate(invoice.due_date)}</TableCell>
                                <TableCell className="text-right">
                                  {invoice.days_overdue > 0 ? (
                                    <Badge variant="destructive">{invoice.days_overdue}</Badge>
                                  ) : (
                                    <Badge variant="secondary">Current</Badge>
                                  )}
                                </TableCell>
                                <TableCell className="text-right font-semibold">
                                  {formatCurrency(invoice.amount)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          No invoices in this bucket
                        </p>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No receivables data available</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
