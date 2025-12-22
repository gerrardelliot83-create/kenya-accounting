import { Badge } from '@/components/ui/badge';
import type { TicketPriority } from '@/types/admin-support';
import { AlertCircle, ArrowUp, Minus, ArrowDown } from 'lucide-react';

interface TicketPriorityBadgeProps {
  priority: TicketPriority;
  showIcon?: boolean;
}

const priorityConfig = {
  urgent: {
    label: 'Urgent',
    variant: 'destructive' as const,
    className: 'bg-red-500 text-white hover:bg-red-600',
    icon: AlertCircle,
  },
  high: {
    label: 'High',
    variant: 'default' as const,
    className: 'bg-orange-500 text-white hover:bg-orange-600',
    icon: ArrowUp,
  },
  medium: {
    label: 'Medium',
    variant: 'secondary' as const,
    className: 'bg-yellow-500 text-white hover:bg-yellow-600',
    icon: Minus,
  },
  low: {
    label: 'Low',
    variant: 'outline' as const,
    className: 'bg-gray-500 text-white hover:bg-gray-600',
    icon: ArrowDown,
  },
};

export const TicketPriorityBadge = ({ priority, showIcon = false }: TicketPriorityBadgeProps) => {
  const config = priorityConfig[priority];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={config.className}>
      {showIcon && <Icon className="mr-1 h-3 w-3" />}
      {config.label}
    </Badge>
  );
};
