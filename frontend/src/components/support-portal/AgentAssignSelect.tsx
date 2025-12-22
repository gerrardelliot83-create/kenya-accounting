import { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useSupportAgents, useAssignTicket } from '@/hooks/useAdminSupport';
import { useAuth } from '@/hooks/useAuth';
import { UserPlus, Loader2 } from 'lucide-react';

interface AgentAssignSelectProps {
  ticketId: string;
  currentAgentId?: string;
  currentAgentName?: string;
  onAssignComplete?: () => void;
}

export const AgentAssignSelect = ({
  ticketId,
  currentAgentId,
  currentAgentName,
  onAssignComplete,
}: AgentAssignSelectProps) => {
  const { user } = useAuth();
  const { data: agents, isLoading: agentsLoading } = useSupportAgents();
  const assignTicket = useAssignTicket();
  const [selectedAgentId, setSelectedAgentId] = useState<string>(currentAgentId || '');

  const handleAssign = () => {
    if (!selectedAgentId) return;

    assignTicket.mutate(
      {
        id: ticketId,
        data: { agent_id: selectedAgentId },
      },
      {
        onSuccess: () => {
          onAssignComplete?.();
        },
      }
    );
  };

  const handleAssignToMe = () => {
    if (!user?.id) return;

    assignTicket.mutate(
      {
        id: ticketId,
        data: { agent_id: user.id },
      },
      {
        onSuccess: () => {
          setSelectedAgentId(user.id);
          onAssignComplete?.();
        },
      }
    );
  };

  if (agentsLoading) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Loading agents...</span>
      </div>
    );
  }

  const isAssigned = !!currentAgentId;
  const isAssignedToMe = currentAgentId === user?.id;
  const hasChanged = selectedAgentId !== currentAgentId && selectedAgentId !== '';

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
        <SelectTrigger className="w-full sm:w-[200px]">
          <SelectValue placeholder="Select agent...">
            {currentAgentName || 'Unassigned'}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="unassigned">Unassigned</SelectItem>
          {agents?.map((agent) => (
            <SelectItem key={agent.id} value={agent.id}>
              {agent.name} ({agent.active_tickets_count} tickets)
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="flex gap-2">
        {hasChanged && (
          <Button
            onClick={handleAssign}
            disabled={assignTicket.isPending}
            size="sm"
          >
            {assignTicket.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Assigning...
              </>
            ) : (
              'Assign'
            )}
          </Button>
        )}

        {!isAssignedToMe && (
          <Button
            onClick={handleAssignToMe}
            disabled={assignTicket.isPending}
            size="sm"
            variant="outline"
          >
            <UserPlus className="mr-2 h-4 w-4" />
            Assign to Me
          </Button>
        )}
      </div>
    </div>
  );
};
