/**
 * Formatting utilities for consistent data display across the application
 */

/**
 * Format a number as KES currency
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
  }).format(amount);
};

/**
 * Format a date string in Kenya locale
 */
export const formatDate = (dateString: string, options?: Intl.DateTimeFormatOptions): string => {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  return new Date(dateString).toLocaleDateString('en-KE', options || defaultOptions);
};

/**
 * Format a date string with long month name
 */
export const formatDateLong = (dateString: string): string => {
  return formatDate(dateString, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

/**
 * Capitalize first letter of a string
 */
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Format a number as a percentage
 */
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${value.toFixed(decimals)}%`;
};
