# Kenya SMB Accounting - Frontend

This is the frontend application for the Kenya SMB Accounting MVP, built with React, TypeScript, and Vite.

## Tech Stack

- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State Management:** Zustand
- **API Client:** Axios
- **Data Fetching:** TanStack React Query
- **UI Components:** Radix UI + Custom Components (Shadcn/UI pattern)
- **Styling:** Tailwind CSS v3
- **Forms:** React Hook Form + Zod validation
- **Authentication:** Supabase Auth + Custom JWT

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components (Button, Input, Card, etc.)
│   │   ├── layout/          # Layout components (Header, Sidebar, MainLayout)
│   │   └── common/          # Common components (ProtectedRoute, LoadingSpinner, ErrorBoundary)
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Library configurations (Supabase, API client, utilities)
│   ├── pages/               # Page components
│   │   ├── auth/            # Login, ChangePassword pages
│   │   └── dashboard/       # Dashboard page
│   ├── routes/              # React Router configuration
│   ├── stores/              # Zustand stores (auth)
│   └── types/               # TypeScript type definitions
├── public/                  # Static assets
└── index.html              # HTML entry point
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running at http://localhost:8000
- Supabase project configured

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials (already configured):
```
VITE_SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000/api/v1
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Features Implemented (Sprint 1)

### Authentication
- Login page with email/password
- Change password flow for first-time users
- Protected routes with role-based access control
- JWT authentication with httpOnly cookies
- Auto-redirect on session expiry

### Layout
- Responsive sidebar navigation
- Mobile-friendly design
- User dropdown with logout
- Role-based menu items

### Dashboard
- Welcome screen
- Account information display
- Placeholder for metrics and activity

### Security
- No sensitive data in localStorage (tokens in httpOnly cookies)
- Input validation with Zod
- Error boundaries for graceful error handling
- Type-safe API client

## Design Principles

### Minimalist UI
- Clean, uncluttered design
- Neutral color palette (grays with minimal accent)
- No decorative elements or emojis
- Generous whitespace

### Mobile-First
- Responsive breakpoints
- Touch-friendly interactions
- Collapsible sidebar on mobile
- Optimized for small screens

### Accessibility
- Semantic HTML
- Proper ARIA labels
- Keyboard navigation
- Focus states
- High contrast ratios

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## Code Quality Standards

### TypeScript
- Strict type checking enabled
- No `any` types allowed
- Explicit return types for functions
- Type-safe API responses

### Component Structure
- Functional components with hooks
- Props interfaces defined
- Single responsibility principle
- Reusable, composable components

### File Organization
- Feature-based structure
- Clear separation of concerns
- Consistent naming conventions

## Future Enhancements

- Invoice management UI
- Expense tracking UI
- Payment processing UI
- Financial reports and charts
- Multi-currency support
- M-Pesa integration UI
- Client management
- Document uploads
- Advanced filtering and search
- Export to PDF/Excel

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

Follow these guidelines when contributing:

1. Write TypeScript with proper types
2. Follow the established component patterns
3. Use Tailwind CSS for styling
4. Ensure mobile responsiveness
5. Add proper error handling
6. Write meaningful commit messages

## License

Proprietary - Kenya SMB Accounting MVP
