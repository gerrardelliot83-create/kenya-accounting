/**
 * Tax-related type definitions for Kenya tax compliance
 */

/**
 * Tax Settings for a business
 */
export interface TaxSettings {
  id: string;
  business_id: string;
  is_vat_registered: boolean;
  vat_registration_number?: string;
  vat_registration_date?: string;
  is_tot_eligible: boolean;
  financial_year_start_month: number;
  created_at: string;
  updated_at: string;
}

/**
 * Request to update tax settings
 */
export interface UpdateTaxSettingsRequest {
  is_vat_registered?: boolean;
  vat_registration_number?: string;
  vat_registration_date?: string;
  is_tot_eligible?: boolean;
  financial_year_start_month?: number;
}

/**
 * VAT Summary for a specific period
 */
export interface VATSummary {
  period_start: string;
  period_end: string;
  output_vat: number;
  input_vat: number;
  net_vat: number;
  total_sales: number;
  total_expenses_with_vat: number;
  vat_rate: number;
}

/**
 * TOT (Turnover Tax) Summary for a specific period
 */
export interface TOTSummary {
  period_start: string;
  period_end: string;
  gross_turnover: number;
  tot_payable: number;
  tot_rate: number;
}

/**
 * Filing Guidance information
 */
export interface FilingGuidance {
  tax_type: 'vat' | 'tot' | 'none';
  next_filing_date: string;
  filing_frequency: string;
  requirements: string[];
  helpful_notes: string[];
}

/**
 * VAT Return export response
 */
export interface VATReturnExport {
  filename: string;
  content: Blob;
}
