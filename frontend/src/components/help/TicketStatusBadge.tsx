import { Badge } from '@/components/ui/badge';
import type { TicketStatus } from '@/types/support';
import { cn } from '@/lib/utils';

interface TicketStatusBadgeProps {
  status: TicketStatus;
  className?: string;
}

const statusConfig: Record<
  TicketStatus,
  {
    label: string;
    variant: 'default' | 'secondary' | 'destructive' | 'outline';
    className: string;
  }
> = {
  open: {
    label: 'Open',
    variant: 'default',
    className: 'bg-blue-500 hover:bg-blue-600 text-white',
  },
  in_progress: {
    label: 'In Progress',
    variant: 'default',
    className: 'bg-yellow-500 hover:bg-yellow-600 text-white',
  },
  waiting_customer: {
    label: 'Waiting for You',
    variant: 'default',
    className: 'bg-orange-500 hover:bg-orange-600 text-white',
  },
  resolved: {
    label: 'Resolved',
    variant: 'default',
    className: 'bg-green-500 hover:bg-green-600 text-white',
  },
  closed: {
    label: 'Closed',
    variant: 'secondary',
    className: 'bg-gray-500 hover:bg-gray-600 text-white',
  },
};

export const TicketStatusBadge = ({ status, className }: TicketStatusBadgeProps) => {
  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} className={cn(config.className, className)}>
      {config.label}
    </Badge>
  );
};
