import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

interface SupportStatCardProps {
  title: string;
  count: number;
  icon: LucideIcon;
  linkTo?: string;
  linkText?: string;
  variant?: 'default' | 'urgent' | 'success';
  description?: string;
}

const variantStyles = {
  default: 'text-blue-600 dark:text-blue-400',
  urgent: 'text-red-600 dark:text-red-400',
  success: 'text-green-600 dark:text-green-400',
};

export const SupportStatCard = ({
  title,
  count,
  icon: Icon,
  linkTo,
  linkText,
  variant = 'default',
  description,
}: SupportStatCardProps) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-5 w-5 ${variantStyles[variant]}`} />
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${variantStyles[variant]}`}>
          {count.toLocaleString()}
        </div>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
        {linkTo && linkText && (
          <Link to={linkTo}>
            <Button variant="link" className="mt-2 h-auto p-0 text-xs">
              {linkText}
              <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </Link>
        )}
      </CardContent>
    </Card>
  );
};
