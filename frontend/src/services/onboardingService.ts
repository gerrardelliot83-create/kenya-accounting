import type {
  Business,
  BusinessCreateData,
  OnboardingItem,
  OnboardingStats,
  OnboardingQueueParams,
  OnboardingQueueResponse,
  OnboardingStatus,
} from '@/types/onboarding';

const STORAGE_KEY = 'onboarding_data';

interface StorageData {
  businesses: Business[];
  queue: OnboardingItem[];
}

// Helper to get data from localStorage
const getStorageData = (): StorageData => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    return JSON.parse(stored);
  }
  return { businesses: [], queue: [] };
};

// Helper to save data to localStorage
const saveStorageData = (data: StorageData): void => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
};

// Helper to get date range
const getDateRange = (type: 'today' | 'week' | 'month'): { start: Date; end: Date } => {
  const now = new Date();
  const start = new Date();
  const end = new Date();

  if (type === 'today') {
    start.setHours(0, 0, 0, 0);
    end.setHours(23, 59, 59, 999);
  } else if (type === 'week') {
    const day = now.getDay();
    const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
    start.setDate(diff);
    start.setHours(0, 0, 0, 0);
  } else if (type === 'month') {
    start.setDate(1);
    start.setHours(0, 0, 0, 0);
  }

  return { start, end };
};

export const onboardingService = {
  /**
   * Create a new business
   */
  async createBusiness(data: BusinessCreateData, agentId: string, agentName: string): Promise<Business> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const storage = getStorageData();

    const businessId = `biz_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const onboardingId = `onb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const createdAt = new Date().toISOString();

    const business: Business = {
      id: businessId,
      name: data.businessInfo.name,
      businessType: data.businessInfo.businessType,
      kraPin: data.businessInfo.kraPin,
      industry: data.businessInfo.industry,
      phone: data.contactInfo.phone,
      email: data.contactInfo.email,
      address: data.contactInfo.address,
      county: data.contactInfo.county,
      taxRegime: data.taxConfig.taxRegime,
      vatNumber: data.taxConfig.vatNumber,
      estimatedAnnualTurnover: data.taxConfig.estimatedAnnualTurnover,
      filingFrequency: data.taxConfig.filingFrequency,
      createdAt,
      createdBy: agentId,
    };

    const onboardingItem: OnboardingItem = {
      id: onboardingId,
      businessId,
      businessName: business.name,
      status: 'completed',
      agentId,
      agentName,
      createdAt,
      completedAt: createdAt,
      notes: `Business created successfully. Primary user: ${data.primaryUser.fullName} (${data.primaryUser.email})`,
    };

    storage.businesses.push(business);
    storage.queue.push(onboardingItem);
    saveStorageData(storage);

    return business;
  },

  /**
   * Get onboarding queue with filtering
   */
  async getOnboardingQueue(params?: OnboardingQueueParams): Promise<OnboardingQueueResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const storage = getStorageData();
    let items = [...storage.queue];

    // Filter by status
    if (params?.status) {
      items = items.filter(item => item.status === params.status);
    }

    // Filter by date range
    if (params?.startDate) {
      const startDate = new Date(params.startDate);
      items = items.filter(item => new Date(item.createdAt) >= startDate);
    }

    if (params?.endDate) {
      const endDate = new Date(params.endDate);
      items = items.filter(item => new Date(item.createdAt) <= endDate);
    }

    // Sort by created date (newest first)
    items.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    const total = items.length;
    const offset = params?.offset || 0;
    const limit = params?.limit || 20;

    // Paginate
    items = items.slice(offset, offset + limit);

    return {
      items,
      total,
      limit,
      offset,
    };
  },

  /**
   * Get onboarding statistics
   */
  async getOnboardingStats(): Promise<OnboardingStats> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));

    const storage = getStorageData();
    const items = storage.queue.filter(item => item.status === 'completed');

    const today = getDateRange('today');
    const week = getDateRange('week');
    const month = getDateRange('month');

    const todayCount = items.filter(item => {
      const date = new Date(item.createdAt);
      return date >= today.start && date <= today.end;
    }).length;

    const weekCount = items.filter(item => {
      const date = new Date(item.createdAt);
      return date >= week.start;
    }).length;

    const monthCount = items.filter(item => {
      const date = new Date(item.createdAt);
      return date >= month.start;
    }).length;

    return {
      // API fields (mock values)
      total_applications: items.length,
      draft: 0,
      submitted: 0,
      under_review: 0,
      approved: items.length,
      rejected: 0,
      info_requested: 0,
      approved_this_month: monthCount,
      avg_processing_days: 0,
      // Local mock fields
      today: todayCount,
      thisWeek: weekCount,
      thisMonth: monthCount,
      total: items.length,
    };
  },

  /**
   * Get recent onboardings
   */
  async getRecentOnboardings(limit: number = 5): Promise<OnboardingItem[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));

    const storage = getStorageData();
    const items = [...storage.queue];

    // Sort by created date (newest first)
    items.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    return items.slice(0, limit);
  },

  /**
   * Update onboarding status
   */
  async updateOnboardingStatus(id: string, status: OnboardingStatus, notes?: string): Promise<OnboardingItem> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const storage = getStorageData();
    const itemIndex = storage.queue.findIndex(item => item.id === id);

    if (itemIndex === -1) {
      throw new Error('Onboarding item not found');
    }

    const item = storage.queue[itemIndex];
    item.status = status;

    if (notes) {
      item.notes = notes;
    }

    if (status === 'completed') {
      item.completedAt = new Date().toISOString();
    }

    storage.queue[itemIndex] = item;
    saveStorageData(storage);

    return item;
  },

  /**
   * Get business by ID
   */
  async getBusiness(id: string): Promise<Business | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));

    const storage = getStorageData();
    return storage.businesses.find(business => business.id === id) || null;
  },
};
