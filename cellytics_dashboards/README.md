# Cellytics Dashboards - Phase 1

This is the **foundational setup** of the Cellytics dashboard application.

## What's Included in Phase 1

✅ **Authentication**

- JWT-based login with FastAPI backend
- Token stored in localStorage
- Automatic token attachment to API requests
- Session restoration on page reload

✅ **Layout Structure**

- Root layout with AuthProvider
- Auth layout for login pages
- Dashboard layout with sidebar + header
- Role-based navigation

✅ **Components**

- Button (with variants)
- Card (with header/body)
- LoadingSpinner
- ErrorAlert & SuccessAlert
- Sidebar (with active state)
- Header (with user dropdown)
- LoginForm

✅ **API Communication**

- Axios client with interceptors
- Error handling
- Request/response helpers
- TypeScript types for all data

✅ **Types & Constants**

- Auth types (User, Login, etc)
- Dashboard types (extensible)
- API error types
- Constants for routes, colors, endpoints

## Folder Structure

```
src/
├── app/                        # Next.js App Router
│   ├── (auth)/                # Auth group (login pages)
│   │   └── login/
│   ├── (dashboard)/           # Dashboard group (protected pages)
│   │   └── [dashboard pages will go here in Phase 2]
│   ├── layout.tsx             # Root layout (AuthProvider)
│   ├── page.tsx               # Landing page
│   └── globals.css            # Tailwind + custom CSS
│
├── components/                # Reusable UI components
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── LoginForm.tsx
│   ├── LoadingSpinner.tsx
│   ├── ErrorAlert.tsx
│   └── SuccessAlert.tsx
│
├── context/                   # Global state
│   └── AuthContext.tsx        # Auth state + login/logout
│
├── lib/                       # Utilities
│   └── api.ts                # Axios client with interceptors
│
├── types/                     # TypeScript types
│   ├── auth.ts               # User, Login, Auth types
│   ├── dashboard.ts          # Dashboard data types
│   └── api.ts                # API response types
│
└── utils/                     # Constants & helpers
    └── constants.ts           # Routes, colors, endpoints
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd cellytics_dashboards
npm install
```

**What this installs:**

- `next` - React framework
- `react` & `react-dom` - UI library
- `typescript` - Type safety
- `tailwindcss` - Styling
- `axios` - HTTP client
- `@tailwindcss/forms` - Form styling

### 2. Configure Environment Variables

Copy `.env.local.example` to `.env.local` and update:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Important:**

- This must match where your FastAPI backend is running
- When developing locally: `http://localhost:8000`
- When deployed to Render: `https://your-backend-url.onrender.com`

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## How It Works

### The Authentication Flow

1. **User visits app** → Lands on `/` (home page) or redirects to `/login`
2. **User enters email/password** → Form submits to LoginForm component
3. **LoginForm calls AuthContext.login()** → Makes POST to `/auth/login` via Axios
4. **Backend returns token + user** → AuthContext saves to localStorage
5. **User redirected to `/dashboard`** → Router detects role and redirects to role-specific page
6. **On page reload** → AuthContext `useEffect` restores session from localStorage

### The Layout Structure

```
RootLayout (/app/layout.tsx)
├─ AuthProvider (wraps everything)
│
├─ AuthLayout (/app/(auth)/layout.tsx)
│  └─ LoginPage (/app/(auth)/login/page.tsx)
│
└─ DashboardLayout (/app/(dashboard)/layout.tsx)
   ├─ Sidebar
   └─ [Dashboard Pages - Phase 2]
```

### API Communication

Every request goes through the Axios client in `lib/api.ts`:

```
Your Component
    ↓
useAuth() or apiClient.post()
    ↓
Axios Request Interceptor (adds token)
    ↓
FastAPI Backend
    ↓
Axios Response Interceptor (checks errors)
    ↓
Your Component (gets data)
```

## Common Beginner Mistakes to Avoid

❌ **Don't:**

- Add Redux/Zustand yet (Context is enough for Phase 1)
- Create custom hooks too early (keep logic in components)
- Over-abstract before understanding the domain
- Make API calls directly (use the apiClient)
- Store sensitive data in localStorage (we only store JWT)

✅ **Do:**

- Keep components small and focused
- Use the shared Button, Card, etc components
- Trust the API client to handle auth
- Let AuthContext be the "single source of truth" for user data
- Read component comments to understand the "why"

## Testing the Setup

### 1. Verify Tailwind is working

- Open [http://localhost:3000](http://localhost:3000)
- See the landing page with navy/gold colors
- Click "Get Started" → Should go to `/login`

### 2. Test the login form

- The form is functional but will fail if backend isn't running
- To test frontend validation, try submitting empty form

### 3. Verify environment variables

- In browser console, you can check:

```javascript
console.log(process.env.NEXT_PUBLIC_API_URL);
// Should print: http://localhost:8000
```

## What's Missing (Phase 2)

🎯 **Phase 2 will add:**

- Dashboard pages for each role (4 pages)
- Sample dashboard data components
- API calls to fetch dashboard data
- Charts/graphs (Recharts)
- Tables/lists of members
- Role-specific widgets

🎯 **Phase 3 will add:**

- More features (reports, filters, exports)
- Deployment to Vercel
- Production optimization

## Troubleshooting

### "Cannot find module @/\*"

- This is the path alias from `tsconfig.json`
- If you get errors, make sure VS Code knows about it:
  - Ctrl+Shift+P → "TypeScript: Restart TS Server"

### "API is not defined"

- Did you import `apiClient` from `@/lib/api`?
- Check the import statement at the top of your file

### Login fails with 401

- Is your FastAPI backend running?
- Is `NEXT_PUBLIC_API_URL` pointing to the right place?
- Check FastAPI logs for the actual error

### Styles not loading

- Clear `.next` folder: `rm -rf .next`
- Restart dev server: `npm run dev`
- Tailwind classes need to match the content paths in `tailwind.config.ts`

## Next Steps

1. **Get backend running** (if not already)
   - Start your FastAPI app locally
   - Test the `/auth/login` endpoint with Postman/Insomnia

2. **Test login**
   - Try logging in with real credentials
   - Check that token is saved in localStorage

3. **Prepare for Phase 2**
   - Look at your FastAPI dashboard endpoints
   - Start thinking about what data each dashboard needs

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Axios Documentation](https://axios-http.com/docs/intro)
- [React Hooks](https://react.dev/reference/react)

---

**Questions?** Check the comments in each file - they explain the "why" behind each piece of code.






Now add the fellowship dashboard. Remember we have a fellowship belonging to a zone. We should be able to see all aggregate stats like total number of senior cells, total numbeer of cells, cells percentage that reported, the total attendance, souls won, finances, grouwth rate, a barchat showing fellowship attendance trends, conversion sources, growth metrics, and synonymous to the zonal dashboard, here we should be able to see the top senior cell/cell of the week. We should also be able to see these aggregate stats over a period of week, month and year like in the zonal dashboard. The fellowship pastor should be able to zoom into senior cells and see the various senior cells and the cells under them, zoom into cells and see full cell reports of various cell leaders submitted (all the data), make comments and validate the report, the fellowship should also be able to ping a senior cell leader or cell leader about an unsubmitted report, also view unsubmitted cells that haven't reported. The fellowship should also create new senior cells and add/assign cells to them. Remember a cell report is submitted to a cell which is under a senior cell that belongs to a fellowship that belongs to a zone, that belongs to a region.


FR-3.3: Fellowship Pastor Dashboard
o List all senior cells in fellowship
o Submission rate: X/Y cells reported
o Aggregated stats: total attendance, souls won, total finances, first-timers
o List of cells needing attention (no report >7 days, declining attendance >20%)
o View any cell report
o Export weekly report (CSV/PDF).

Understand our reqs, the nextjs structure, backend structure and neatly integrate the new fellowship dashboard, matching our brand, test it and deploy to a new branch.
