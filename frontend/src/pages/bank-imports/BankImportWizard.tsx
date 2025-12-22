import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, ChevronLeft, ChevronRight, Check, FileText, FileSpreadsheet, File } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  useCreateBankImport,
  useUpdateColumnMapping,
  useProcessImport,
  useImportPreview,
  useBankImport,
} from '@/hooks/useBankImports';
import type { SourceBank, ColumnMapping } from '@/types/bank-import';
import { cn } from '@/lib/utils';

type WizardStep = 'upload' | 'mapping' | 'preview' | 'import';

const STEPS: { id: WizardStep; label: string; description: string }[] = [
  { id: 'upload', label: 'Upload File', description: 'Choose bank statement file' },
  { id: 'mapping', label: 'Column Mapping', description: 'Map columns to fields' },
  { id: 'preview', label: 'Preview', description: 'Review mapped data' },
  { id: 'import', label: 'Import', description: 'Process transactions' },
];

const TARGET_FIELDS = [
  { value: 'date', label: 'Transaction Date' },
  { value: 'description', label: 'Description' },
  { value: 'debit', label: 'Debit Amount' },
  { value: 'credit', label: 'Credit Amount' },
  { value: 'balance', label: 'Balance' },
  { value: 'reference', label: 'Reference' },
  { value: null, label: 'Ignore Column' },
] as const;

export const BankImportWizard = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<WizardStep>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceBank, setSourceBank] = useState<SourceBank>('other');
  const [importId, setImportId] = useState<string>('');
  const [columnMappings, setColumnMappings] = useState<ColumnMapping[]>([]);
  const [detectedColumns, setDetectedColumns] = useState<string[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const createImport = useCreateBankImport();
  const updateMapping = useUpdateColumnMapping();
  const processImport = useProcessImport();
  const { data: importData } = useBankImport(importId);
  const { data: previewData } = useImportPreview(importId);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleUploadNext = async () => {
    if (!selectedFile || !sourceBank) return;

    try {
      const result = await createImport.mutateAsync({ file: selectedFile, sourceBank });
      setImportId(result.id);

      // Auto-detect columns from the result or set initial mappings
      if (result.columnMappings && result.columnMappings.length > 0) {
        setColumnMappings(result.columnMappings);
        setDetectedColumns(result.columnMappings.map(m => m.sourceColumn));
      }

      setCurrentStep('mapping');
    } catch (error) {
      console.error('Failed to upload file:', error);
    }
  };

  const handleMappingChange = (sourceColumn: string, targetField: string | null) => {
    setColumnMappings((prev) => {
      const existing = prev.filter((m) => m.sourceColumn !== sourceColumn);
      return [
        ...existing,
        {
          sourceColumn,
          targetField: targetField as ColumnMapping['targetField'],
        },
      ];
    });
  };

  const handleMappingNext = async () => {
    if (!importId) return;

    try {
      await updateMapping.mutateAsync({
        id: importId,
        data: { columnMappings },
      });
      setCurrentStep('preview');
    } catch (error) {
      console.error('Failed to update mapping:', error);
    }
  };

  const handlePreviewNext = () => {
    setCurrentStep('import');
    handleProcessImport();
  };

  const handleProcessImport = async () => {
    if (!importId) return;

    try {
      // Simulate progress
      setUploadProgress(0);
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      await processImport.mutateAsync({ id: importId });

      clearInterval(interval);
      setUploadProgress(100);

      // Navigate to detail page after a short delay
      setTimeout(() => {
        navigate(`/bank-imports/${importId}`);
      }, 1500);
    } catch (error) {
      console.error('Failed to process import:', error);
    }
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return <FileSpreadsheet className="h-8 w-8 text-green-600" />;
      case 'pdf':
        return <FileText className="h-8 w-8 text-red-600" />;
      default:
        return <File className="h-8 w-8 text-gray-600" />;
    }
  };

  const getTargetFieldLabel = (field: ColumnMapping['targetField']) => {
    const found = TARGET_FIELDS.find((f) => f.value === field);
    return found?.label || 'Ignore Column';
  };

  const isStepComplete = (step: WizardStep): boolean => {
    const stepIndex = STEPS.findIndex((s) => s.id === step);
    const currentIndex = STEPS.findIndex((s) => s.id === currentStep);
    return stepIndex < currentIndex;
  };

  const canProceed = (): boolean => {
    switch (currentStep) {
      case 'upload':
        return !!selectedFile && !!sourceBank;
      case 'mapping':
        // At least date and description must be mapped, and at least one of debit/credit
        const hasDate = columnMappings.some((m) => m.targetField === 'date');
        const hasDescription = columnMappings.some((m) => m.targetField === 'description');
        const hasAmount = columnMappings.some((m) => m.targetField === 'debit' || m.targetField === 'credit');
        return hasDate && hasDescription && hasAmount;
      case 'preview':
        return true;
      case 'import':
        return false;
      default:
        return false;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Import Bank Statement</h1>
          <p className="mt-2 text-muted-foreground">
            Upload and map your bank statement to reconcile transactions
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/bank-imports')}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back to Imports
        </Button>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => (
          <div key={step.id} className="flex flex-1 items-center">
            <div className="flex flex-col items-center flex-1">
              <div
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors',
                  currentStep === step.id
                    ? 'border-primary bg-primary text-primary-foreground'
                    : isStepComplete(step.id)
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-muted-foreground/30 bg-background'
                )}
              >
                {isStepComplete(step.id) ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>
              <div className="mt-2 text-center">
                <p className="text-sm font-medium">{step.label}</p>
                <p className="text-xs text-muted-foreground">{step.description}</p>
              </div>
            </div>
            {index < STEPS.length - 1 && (
              <div
                className={cn(
                  'h-0.5 flex-1 mx-4 mb-8 transition-colors',
                  isStepComplete(STEPS[index + 1].id)
                    ? 'bg-primary'
                    : 'bg-muted-foreground/30'
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {/* Step 1: Upload */}
          {currentStep === 'upload' && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="sourceBank">Source Bank</Label>
                <Select value={sourceBank} onValueChange={(value) => setSourceBank(value as SourceBank)}>
                  <SelectTrigger id="sourceBank">
                    <SelectValue placeholder="Select bank" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="equity">Equity Bank</SelectItem>
                    <SelectItem value="kcb">KCB</SelectItem>
                    <SelectItem value="cooperative">Co-operative Bank</SelectItem>
                    <SelectItem value="mpesa">M-Pesa</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-12 text-center transition-colors',
                  isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/30',
                  selectedFile && 'border-green-600 bg-green-50'
                )}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                {selectedFile ? (
                  <div className="flex flex-col items-center gap-4">
                    {getFileIcon(selectedFile.name)}
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFile(null)}
                    >
                      Remove File
                    </Button>
                  </div>
                ) : (
                  <>
                    <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                    <div className="mt-4">
                      <p className="text-lg font-medium">
                        Drag and drop your bank statement here
                      </p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        or click to browse files
                      </p>
                    </div>
                    <div className="mt-4 flex gap-2 justify-center">
                      <Badge variant="secondary">CSV</Badge>
                      <Badge variant="secondary">PDF</Badge>
                      <Badge variant="secondary">OFX</Badge>
                    </div>
                    <input
                      type="file"
                      className="mt-4 mx-auto block text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                      accept=".csv,.pdf,.ofx"
                      onChange={handleFileSelect}
                    />
                  </>
                )}
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleUploadNext}
                  disabled={!canProceed() || createImport.isPending}
                >
                  {createImport.isPending ? 'Uploading...' : 'Next'}
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Column Mapping */}
          {currentStep === 'mapping' && (
            <div className="space-y-6">
              <Alert>
                <AlertDescription>
                  Map the columns from your bank statement to the corresponding fields. Date, Description, and at least one amount field (Debit or Credit) are required.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                {detectedColumns.length > 0 ? (
                  detectedColumns.map((column) => {
                    const mapping = columnMappings.find((m) => m.sourceColumn === column);
                    return (
                      <div key={column} className="flex items-center gap-4">
                        <div className="flex-1">
                          <Label className="text-sm font-medium">{column}</Label>
                        </div>
                        <div className="flex-1">
                          <Select
                            value={mapping?.targetField || ''}
                            onValueChange={(value) =>
                              handleMappingChange(column, value === '' ? null : value)
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select field" />
                            </SelectTrigger>
                            <SelectContent>
                              {TARGET_FIELDS.map((field) => (
                                <SelectItem
                                  key={String(field.value)}
                                  value={String(field.value)}
                                >
                                  {field.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No columns detected. Please go back and upload a valid file.
                  </p>
                )}
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep('upload')}>
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
                <Button
                  onClick={handleMappingNext}
                  disabled={!canProceed() || updateMapping.isPending}
                >
                  {updateMapping.isPending ? 'Saving...' : 'Next'}
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Preview */}
          {currentStep === 'preview' && (
            <div className="space-y-6">
              <Alert>
                <AlertDescription>
                  Review the first 10 rows of your mapped data. If everything looks correct, proceed to import.
                </AlertDescription>
              </Alert>

              {previewData && previewData.rows.length > 0 ? (
                <div className="rounded-md border overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {columnMappings
                          .filter((m) => m.targetField !== null)
                          .map((m) => (
                            <TableHead key={m.sourceColumn}>
                              {getTargetFieldLabel(m.targetField)}
                            </TableHead>
                          ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {previewData.rows.slice(0, 10).map((row, index) => (
                        <TableRow key={index}>
                          {columnMappings
                            .filter((m) => m.targetField !== null)
                            .map((m) => (
                              <TableCell key={m.sourceColumn}>
                                {row[m.sourceColumn] || '-'}
                              </TableCell>
                            ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Loading preview data...
                </p>
              )}

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep('mapping')}>
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Back to Mapping
                </Button>
                <Button onClick={handlePreviewNext}>
                  Import Transactions
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Import */}
          {currentStep === 'import' && (
            <div className="space-y-6">
              <div className="text-center py-12">
                <div className="mx-auto mb-6">
                  {uploadProgress === 100 ? (
                    <div className="h-16 w-16 mx-auto rounded-full bg-green-100 flex items-center justify-center">
                      <Check className="h-8 w-8 text-green-600" />
                    </div>
                  ) : (
                    <div className="h-16 w-16 mx-auto rounded-full border-4 border-primary border-t-transparent animate-spin" />
                  )}
                </div>

                <h3 className="text-xl font-semibold mb-2">
                  {uploadProgress === 100 ? 'Import Complete!' : 'Processing Import...'}
                </h3>
                <p className="text-muted-foreground mb-6">
                  {uploadProgress === 100
                    ? 'Your bank transactions have been imported successfully.'
                    : 'Please wait while we process your bank statement.'}
                </p>

                <Progress value={uploadProgress} className="w-full max-w-md mx-auto" />

                {importData && uploadProgress === 100 && (
                  <div className="mt-6 grid grid-cols-3 gap-4 max-w-md mx-auto">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-2xl font-bold">{importData.totalRows}</p>
                      <p className="text-sm text-muted-foreground">Total</p>
                    </div>
                    <div className="p-4 bg-green-100 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{importData.matchedRows}</p>
                      <p className="text-sm text-muted-foreground">Matched</p>
                    </div>
                    <div className="p-4 bg-yellow-100 rounded-lg">
                      <p className="text-2xl font-bold text-yellow-600">{importData.unmatchedRows}</p>
                      <p className="text-sm text-muted-foreground">Unmatched</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
