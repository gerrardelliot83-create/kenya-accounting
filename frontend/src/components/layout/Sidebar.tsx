import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Users,
  Settings,
  Receipt,
  CreditCard,
  X,
  Package,
  Landmark,
  LifeBuoy,
  Calculator,
  BarChart3,
  Building2,
  Shield,
  Server,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import type { UserRole } from '@/types/auth';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: UserRole[];
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    roles: ['business_admin', 'bookkeeper', 'onboarding_agent', 'support_agent', 'system_admin'],
  },
  {
    name: 'Contacts',
    href: '/contacts',
    icon: Users,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Items',
    href: '/items',
    icon: Package,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Invoices',
    href: '/invoices',
    icon: FileText,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Expenses',
    href: '/expenses',
    icon: Receipt,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Bank Import',
    href: '/bank-imports',
    icon: Landmark,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Tax',
    href: '/tax',
    icon: Calculator,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: BarChart3,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Payments',
    href: '/payments',
    icon: CreditCard,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Help & Support',
    href: '/help',
    icon: LifeBuoy,
    roles: ['business_admin', 'bookkeeper'],
  },
  {
    name: 'Clients',
    href: '/clients',
    icon: Users,
    roles: ['onboarding_agent', 'support_agent', 'system_admin'],
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    roles: ['business_admin', 'bookkeeper', 'onboarding_agent', 'support_agent', 'system_admin'],
  },
];

const adminNavItems: NavItem[] = [
  {
    name: 'Admin Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
    roles: ['system_admin'],
  },
  {
    name: 'Businesses',
    href: '/admin/businesses',
    icon: Building2,
    roles: ['system_admin'],
  },
  {
    name: 'Internal Users',
    href: '/admin/users',
    icon: Shield,
    roles: ['system_admin'],
  },
  {
    name: 'Audit Logs',
    href: '/admin/audit-logs',
    icon: FileText,
    roles: ['system_admin'],
  },
  {
    name: 'System Health',
    href: '/admin/system',
    icon: Server,
    roles: ['system_admin'],
  },
];

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const { user } = useAuth();

  const filteredNavItems = navItems.filter((item) =>
    user ? item.roles.includes(user.role) : false
  );

  const filteredAdminNavItems = adminNavItems.filter((item) =>
    user ? item.roles.includes(user.role) : false
  );

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform border-r bg-background transition-transform duration-300 ease-in-out md:static md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Mobile close button */}
          <div className="flex h-16 items-center justify-between px-4 md:hidden">
            <span className="font-semibold">Menu</span>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <Separator className="md:hidden" />

          {/* Navigation */}
          <nav className="flex-1 space-y-1 overflow-y-auto p-4">
            {/* Regular Navigation Items */}
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-secondary text-secondary-foreground'
                        : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
                    )
                  }
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}

            {/* Admin Section */}
            {filteredAdminNavItems.length > 0 && (
              <>
                <Separator className="my-4" />
                <div className="px-3 py-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Administration
                  </p>
                </div>
                {filteredAdminNavItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.href}
                      to={item.href}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                          isActive
                            ? 'bg-secondary text-secondary-foreground'
                            : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
                        )
                      }
                    >
                      <Icon className="h-5 w-5" />
                      <span>{item.name}</span>
                    </NavLink>
                  );
                })}
              </>
            )}
          </nav>
        </div>
      </aside>
    </>
  );
};
