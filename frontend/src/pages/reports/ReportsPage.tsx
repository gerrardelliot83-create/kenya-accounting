import { useNavigate } from 'react-router-dom';
import { TrendingUp, Receipt, Clock, DollarSign } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const reports = [
  {
    id: 'profit-loss',
    title: 'Profit & Loss',
    description: 'View revenue, expenses, and profitability',
    icon: TrendingUp,
    path: '/reports/profit-loss',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    id: 'expenses',
    title: 'Expense Summary',
    description: 'Breakdown of expenses by category',
    icon: Receipt,
    path: '/reports/expenses',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
  {
    id: 'receivables',
    title: 'Aged Receivables',
    description: 'Outstanding invoices and aging analysis',
    icon: Clock,
    path: '/reports/receivables',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  {
    id: 'sales',
    title: 'Sales Summary',
    description: 'Sales breakdown by customer and item',
    icon: DollarSign,
    path: '/reports/sales',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
];

export const ReportsPage = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold">Reports</h1>
        <p className="mt-2 text-muted-foreground">
          Generate and view financial reports for your business
        </p>
      </div>

      {/* Report Cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {reports.map((report) => {
          const Icon = report.icon;
          return (
            <Card
              key={report.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => navigate(report.path)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl">{report.title}</CardTitle>
                    <CardDescription className="mt-2">{report.description}</CardDescription>
                  </div>
                  <div className={`${report.bgColor} p-3 rounded-lg`}>
                    <Icon className={`h-6 w-6 ${report.color}`} />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-primary hover:underline">
                  View Report →
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
