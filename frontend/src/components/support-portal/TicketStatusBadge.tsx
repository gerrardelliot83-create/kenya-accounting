import { Badge } from '@/components/ui/badge';
import type { TicketStatus } from '@/types/admin-support';
import { Circle, Clock, HelpCircle, CheckCircle, XCircle } from 'lucide-react';

interface TicketStatusBadgeProps {
  status: TicketStatus;
  showIcon?: boolean;
}

const statusConfig = {
  open: {
    label: 'Open',
    variant: 'default' as const,
    className: 'bg-blue-500 text-white hover:bg-blue-600',
    icon: Circle,
  },
  in_progress: {
    label: 'In Progress',
    variant: 'secondary' as const,
    className: 'bg-yellow-500 text-white hover:bg-yellow-600',
    icon: Clock,
  },
  waiting_customer: {
    label: 'Waiting Customer',
    variant: 'default' as const,
    className: 'bg-orange-500 text-white hover:bg-orange-600',
    icon: HelpCircle,
  },
  resolved: {
    label: 'Resolved',
    variant: 'default' as const,
    className: 'bg-green-500 text-white hover:bg-green-600',
    icon: CheckCircle,
  },
  closed: {
    label: 'Closed',
    variant: 'outline' as const,
    className: 'bg-gray-500 text-white hover:bg-gray-600',
    icon: XCircle,
  },
};

export const TicketStatusBadge = ({ status, showIcon = false }: TicketStatusBadgeProps) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={config.className}>
      {showIcon && <Icon className="mr-1 h-3 w-3" />}
      {config.label}
    </Badge>
  );
};
