/**
 * Validates Kenyan KRA PIN format
 * Format: Letter + 9 digits + Letter (e.g., A123456789Z)
 */
export const validateKraPin = (pin: string): boolean => {
  const kraRegex = /^[A-Z]\d{9}[A-Z]$/;
  return kraRegex.test(pin);
};

/**
 * Validates Kenyan phone number format
 * Accepts: +254XXXXXXXXX or 07XXXXXXXX or 01XXXXXXXX
 */
export const validateKenyanPhone = (phone: string): boolean => {
  const phoneRegex = /^(\+254|0)[17]\d{8}$/;
  return phoneRegex.test(phone);
};

/**
 * Formats Kenyan phone number to international format
 * Converts 07XXXXXXXX to +254XXXXXXXXX
 */
export const formatKenyanPhone = (phone: string): string => {
  if (phone.startsWith('0')) {
    return `+254${phone.slice(1)}`;
  }
  return phone;
};

/**
 * Validates VAT registration number format
 * Basic validation - checks if it's alphanumeric and has reasonable length
 */
export const validateVatNumber = (vatNumber: string): boolean => {
  // VAT numbers in Kenya typically start with 'P' followed by 9 digits
  const vatRegex = /^P\d{9}[A-Z]?$/;
  return vatRegex.test(vatNumber);
};

/**
 * Generates a temporary password
 * Format: 8 characters with uppercase, lowercase, numbers, and special chars
 */
/**
 * Validates Kenyan National ID format
 * Format: 8 digits
 */
export const validateKenyanId = (id: string): boolean => {
  const idRegex = /^\d{8}$/;
  return idRegex.test(id);
};

export const generateTemporaryPassword = (): string => {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const numbers = '0123456789';
  const special = '!@#$%&*';

  const all = uppercase + lowercase + numbers + special;

  // Ensure at least one of each type
  let password = '';
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];
  password += special[Math.floor(Math.random() * special.length)];

  // Fill remaining with random characters
  for (let i = 4; i < 12; i++) {
    password += all[Math.floor(Math.random() * all.length)];
  }

  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('');
};
