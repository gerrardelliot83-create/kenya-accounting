import { Badge } from '@/components/ui/badge';
import { Eye, EyeOff } from 'lucide-react';

interface InternalNoteBadgeProps {
  className?: string;
}

export const InternalNoteBadge = ({ className }: InternalNoteBadgeProps) => {
  return (
    <Badge variant="secondary" className={className}>
      <EyeOff className="mr-1 h-3 w-3" />
      Internal Note
    </Badge>
  );
};

interface InternalNoteAlertProps {
  className?: string;
}

export const InternalNoteAlert = ({ className }: InternalNoteAlertProps) => {
  return (
    <div className={`flex items-center gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300 ${className}`}>
      <Eye className="h-4 w-4" />
      <span className="font-medium">This is an internal note - not visible to the customer</span>
    </div>
  );
};
