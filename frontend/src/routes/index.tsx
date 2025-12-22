import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';
import { MainLayout } from '@/components/layout/MainLayout';
import { OnboardingLayout } from '@/components/layout/OnboardingLayout';
import { SupportPortalLayout } from '@/components/layout/SupportPortalLayout';
import { LoginPage } from '@/pages/auth/LoginPage';
import { ChangePasswordPage } from '@/pages/auth/ChangePasswordPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { ContactsPage } from '@/pages/contacts/ContactsPage';
import { ItemsPage } from '@/pages/items/ItemsPage';
import { InvoicesPage } from '@/pages/invoices/InvoicesPage';
import { InvoiceFormPage } from '@/pages/invoices/InvoiceFormPage';
import { InvoiceDetailPage } from '@/pages/invoices/InvoiceDetailPage';
import { ExpensesPage } from '@/pages/expenses/ExpensesPage';
import { BankImportsPage, BankImportWizard, BankImportDetailPage } from '@/pages/bank-imports';
import { TaxDashboardPage } from '@/pages/tax';
import { ReportsPage, ProfitLossPage, ExpenseSummaryPage, AgedReceivablesPage, SalesSummaryPage } from '@/pages/reports';
import {
  HelpCentrePage,
  FaqCategoryPage,
  FaqSearchResultsPage,
  HelpArticlePage,
  MyTicketsPage,
  TicketDetailPage,
  CreateTicketPage,
} from '@/pages/help';
import { OnboardingDashboardPage } from '@/pages/onboarding/OnboardingDashboardPage';
import { CreateBusinessPage } from '@/pages/onboarding/CreateBusinessPage';
import { OnboardingQueuePage } from '@/pages/onboarding/OnboardingQueuePage';
import { ApplicationDetailPage } from '@/pages/onboarding/ApplicationDetailPage';
import { OnboardingSettingsPage } from '@/pages/onboarding/OnboardingSettingsPage';
import { SupportDashboardPage, SupportTicketListPage, SupportTicketDetailPage } from '@/pages/support-portal';
import {
  AdminDashboardPage,
  BusinessDirectoryPage,
  BusinessDetailPage,
  InternalUsersPage,
  AuditLogViewerPage,
  SystemHealthPage,
} from '@/pages/admin';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { NotFoundPage } from '@/pages/NotFoundPage';

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />

          {/* Contacts routes */}
          <Route path="contacts" element={<ContactsPage />} />

          {/* Items routes */}
          <Route path="items" element={<ItemsPage />} />

          {/* Invoices routes */}
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="invoices/new" element={<InvoiceFormPage />} />
          <Route path="invoices/:id" element={<InvoiceDetailPage />} />
          <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />

          {/* Expenses routes */}
          <Route path="expenses" element={<ExpensesPage />} />

          {/* Bank Imports routes */}
          <Route path="bank-imports" element={<BankImportsPage />} />
          <Route path="bank-imports/new" element={<BankImportWizard />} />
          <Route path="bank-imports/:id" element={<BankImportDetailPage />} />

          {/* Tax routes */}
          <Route path="tax" element={<TaxDashboardPage />} />

          {/* Reports routes */}
          <Route path="reports" element={<ReportsPage />} />
          <Route path="reports/profit-loss" element={<ProfitLossPage />} />
          <Route path="reports/expenses" element={<ExpenseSummaryPage />} />
          <Route path="reports/receivables" element={<AgedReceivablesPage />} />
          <Route path="reports/sales" element={<SalesSummaryPage />} />

          {/* Help & Support routes */}
          <Route path="help" element={<HelpCentrePage />} />
          <Route path="help/faq/:categoryId" element={<FaqCategoryPage />} />
          <Route path="help/faq/search" element={<FaqSearchResultsPage />} />
          <Route path="help/articles/:slug" element={<HelpArticlePage />} />
          <Route path="help/tickets" element={<MyTicketsPage />} />
          <Route path="help/tickets/new" element={<CreateTicketPage />} />
          <Route path="help/tickets/:id" element={<TicketDetailPage />} />

          {/* Placeholder routes for future implementation */}
          <Route path="payments" element={<div>Payments - Coming Soon</div>} />
          <Route path="clients" element={<div>Clients - Coming Soon</div>} />
          <Route path="settings" element={<div>Settings - Coming Soon</div>} />
        </Route>

        {/* Change password route (protected but outside main layout) */}
        <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />

        {/* Onboarding Portal - Role-restricted routes */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute allowedRoles={['onboarding_agent', 'system_admin']}>
              <OnboardingLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<OnboardingDashboardPage />} />
          <Route path="create" element={<CreateBusinessPage />} />
          <Route path="queue" element={<OnboardingQueuePage />} />
          <Route path="applications/:id" element={<ApplicationDetailPage />} />
          <Route path="settings" element={<OnboardingSettingsPage />} />
        </Route>

        {/* Support Portal - Role-restricted routes */}
        <Route
          path="/support-portal"
          element={
            <ProtectedRoute allowedRoles={['support_agent', 'system_admin']}>
              <SupportPortalLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<SupportDashboardPage />} />
          <Route path="tickets" element={<SupportTicketListPage />} />
          <Route path="tickets/:id" element={<SupportTicketDetailPage />} />
          <Route path="my-tickets" element={<SupportTicketListPage />} />
          <Route path="settings" element={<div>Support Settings - Coming Soon</div>} />
        </Route>

        {/* Admin Portal - System Admin Only */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['system_admin']}>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="businesses" element={<BusinessDirectoryPage />} />
          <Route path="businesses/:id" element={<BusinessDetailPage />} />
          <Route path="users" element={<InternalUsersPage />} />
          <Route path="audit-logs" element={<AuditLogViewerPage />} />
          <Route path="system" element={<SystemHealthPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};
