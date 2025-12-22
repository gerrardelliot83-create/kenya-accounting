import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Check,
  X,
  Receipt,
  FileText,
  TrendingUp,
  Calendar,
  DollarSign,
  Tag,
  User,
  AlertCircle,
} from 'lucide-react';
import {
  useReconciliationSuggestions,
  useMatchTransaction,
  useIgnoreTransaction,
} from '@/hooks/useBankImports';
import type { BankTransaction, ReconciliationSuggestion } from '@/types/bank-import';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { cn } from '@/lib/utils';

interface ReconciliationModalProps {
  open: boolean;
  onClose: () => void;
  transaction: BankTransaction;
}

export const ReconciliationModal = ({
  open,
  onClose,
  transaction,
}: ReconciliationModalProps) => {
  const [selectedSuggestion, setSelectedSuggestion] = useState<ReconciliationSuggestion | null>(null);

  const { data: suggestions, isLoading } = useReconciliationSuggestions(transaction.id);
  const matchTransaction = useMatchTransaction();
  const ignoreTransaction = useIgnoreTransaction();

  const handleConfirmMatch = async () => {
    if (!selectedSuggestion) return;

    try {
      await matchTransaction.mutateAsync({
        transactionId: transaction.id,
        data: {
          matchType: selectedSuggestion.matchType,
          matchId: selectedSuggestion.matchId,
        },
      });
      onClose();
    } catch (error) {
      console.error('Failed to match transaction:', error);
    }
  };

  const handleIgnore = async () => {
    if (window.confirm('Are you sure you want to ignore this transaction?')) {
      try {
        await ignoreTransaction.mutateAsync(transaction.id);
        onClose();
      } catch (error) {
        console.error('Failed to ignore transaction:', error);
      }
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600 bg-green-100';
    if (confidence >= 60) return 'text-blue-600 bg-blue-100';
    if (confidence >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return 'High Match';
    if (confidence >= 60) return 'Good Match';
    if (confidence >= 40) return 'Possible Match';
    return 'Low Match';
  };

  const transactionAmount = transaction.debit || transaction.credit || 0;
  const isDebit = !!transaction.debit;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Match Transaction</DialogTitle>
          <DialogDescription>
            Review suggested matches for this bank transaction
          </DialogDescription>
        </DialogHeader>

        {/* Transaction Details */}
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                  <Calendar className="h-4 w-4" />
                  Date
                </div>
                <div className="font-medium">{formatDate(transaction.transactionDate)}</div>
              </div>

              <div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                  <DollarSign className="h-4 w-4" />
                  Amount
                </div>
                <div className={cn('font-medium', isDebit ? 'text-red-600' : 'text-green-600')}>
                  {formatCurrency(transactionAmount)}
                  <span className="text-xs ml-1">{isDebit ? '(Debit)' : '(Credit)'}</span>
                </div>
              </div>

              <div className="col-span-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                  <FileText className="h-4 w-4" />
                  Description
                </div>
                <div className="font-medium truncate">{transaction.description}</div>
              </div>

              {transaction.reference && (
                <div className="col-span-2 md:col-span-4">
                  <div className="text-sm text-muted-foreground mb-1">Reference</div>
                  <div className="font-mono text-sm">{transaction.reference}</div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Separator />

        {/* Suggestions List */}
        <div className="space-y-4">
          <h3 className="font-semibold">Suggested Matches</h3>

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <Card key={index}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <Skeleton className="h-10 w-10 rounded-full" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : suggestions && suggestions.length > 0 ? (
            <div className="space-y-3">
              {suggestions.map((suggestion) => (
                <Card
                  key={suggestion.id}
                  className={cn(
                    'cursor-pointer transition-all hover:shadow-md',
                    selectedSuggestion?.id === suggestion.id &&
                      'ring-2 ring-primary border-primary'
                  )}
                  onClick={() => setSelectedSuggestion(suggestion)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div
                        className={cn(
                          'h-10 w-10 rounded-full flex items-center justify-center',
                          suggestion.matchType === 'expense'
                            ? 'bg-red-100'
                            : 'bg-green-100'
                        )}
                      >
                        {suggestion.matchType === 'expense' ? (
                          <Receipt className="h-5 w-5 text-red-600" />
                        ) : (
                          <FileText className="h-5 w-5 text-green-600" />
                        )}
                      </div>

                      {/* Details */}
                      <div className="flex-1 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">
                                {suggestion.matchType === 'expense' ? 'Expense' : 'Invoice'}
                              </Badge>
                              {suggestion.invoiceNumber && (
                                <span className="text-sm text-muted-foreground">
                                  #{suggestion.invoiceNumber}
                                </span>
                              )}
                            </div>
                            <p className="font-medium mt-1">{suggestion.description}</p>
                          </div>

                          {/* Confidence Badge */}
                          <div className="flex flex-col items-end gap-1">
                            <Badge
                              className={cn(
                                'font-semibold',
                                getConfidenceColor(suggestion.confidence)
                              )}
                            >
                              {suggestion.confidence}%
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {getConfidenceLabel(suggestion.confidence)}
                            </span>
                          </div>
                        </div>

                        {/* Match Details */}
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="flex items-center gap-1 text-muted-foreground">
                              <DollarSign className="h-3 w-3" />
                              Amount
                            </div>
                            <div className="font-medium">{formatCurrency(suggestion.amount)}</div>
                          </div>

                          <div>
                            <div className="flex items-center gap-1 text-muted-foreground">
                              <Calendar className="h-3 w-3" />
                              Date
                            </div>
                            <div className="font-medium">{formatDate(suggestion.date)}</div>
                          </div>

                          {suggestion.category && (
                            <div>
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <Tag className="h-3 w-3" />
                                Category
                              </div>
                              <div className="font-medium">{suggestion.category}</div>
                            </div>
                          )}

                          {suggestion.contactName && (
                            <div>
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <User className="h-3 w-3" />
                                Contact
                              </div>
                              <div className="font-medium truncate">
                                {suggestion.contactName}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Match Reasons */}
                        {suggestion.reasons.length > 0 && (
                          <div className="pt-2">
                            <div className="flex items-start gap-2">
                              <TrendingUp className="h-4 w-4 text-muted-foreground mt-0.5" />
                              <div className="flex-1">
                                <div className="text-xs text-muted-foreground mb-1">
                                  Match reasons:
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {suggestion.reasons.map((reason, index) => (
                                    <Badge key={index} variant="secondary" className="text-xs">
                                      {reason}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Selection Indicator */}
                      {selectedSuggestion?.id === suggestion.id && (
                        <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                          <Check className="h-4 w-4 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No matching expenses or invoices found for this transaction. You can ignore this
                transaction or manually create a matching record.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button variant="outline" onClick={handleIgnore} disabled={ignoreTransaction.isPending}>
            <X className="mr-2 h-4 w-4" />
            Ignore Transaction
          </Button>

          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmMatch}
              disabled={!selectedSuggestion || matchTransaction.isPending}
            >
              <Check className="mr-2 h-4 w-4" />
              {matchTransaction.isPending ? 'Matching...' : 'Confirm Match'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
