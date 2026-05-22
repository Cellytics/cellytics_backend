# QUICK START GUIDE

This guide assumes you're a beginner in Next.js but experienced in backend engineering.

## Before You Start

Make sure you have:

- Node.js 18+ installed (`node --version`)
- npm or yarn (`npm --version`)
- Your FastAPI backend running locally or on Render
- A code editor (VS Code recommended)

## Installation (5 minutes)

```bash
# 1. Navigate to project
cd cellytics_dashboards

# 2. Install all dependencies
npm install

# 3. Check environment is set
# Your .env.local should have:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running Locally (3 minutes)

```bash
# Start the dev server
npm run dev

# Open browser
# http://localhost:3000
```

You should see:

1. A landing page with navy/gold branding
2. "Get Started" button → takes you to login
3. Login form asking for email/password

## Understanding the Code

### Key Files You'll Interact With

| File                          | Purpose            | You Need to Know                     |
| ----------------------------- | ------------------ | ------------------------------------ |
| `src/context/AuthContext.tsx` | Login/logout state | "The brain" - handles auth           |
| `src/lib/api.ts`              | HTTP client        | Automatically adds token to requests |
| `src/components/`             | UI building blocks | Copy/paste to reuse                  |
| `.env.local`                  | Configuration      | Points to your FastAPI               |
| `package.json`                | Dependencies       | What libraries are installed         |

### The Main Mental Model

```
Your React Component
        ↓
const { login } = useAuth()  ← Get auth functions
        ↓
login(email, password)  ← Make request
        ↓
authContext calls apiClient.post('/auth/login')  ← Axios sends request
        ↓
FastAPI Backend responds
        ↓
Token saved to localStorage
        ↓
Component renders with user data
```

## File Naming Conventions

- **PascalCase for components**: `Button.tsx`, `LoginForm.tsx`
- **camelCase for hooks/utilities**: `useAuth.ts`, `api.ts`
- **kebab-case for routes**: `/auth/login`, `/dashboard/cell-leader`

## Modifying Tailwind Colors

The colors are defined in `tailwind.config.ts`:

```typescript
colors: {
  gold: '#C9A646',
  navy: '#10295B',
  'forest-green': '#10B981',
  'orange-accent': '#F97316',
  'red-alert': '#EF4444',
}
```

Use them in components:

```tsx
<div className="bg-navy text-gold">...</div>
```

## Common Commands

```bash
# Development
npm run dev          # Start dev server

# Production
npm run build        # Build for production
npm run start        # Start production server

# Code quality
npm run lint         # Check for errors
npm run type-check   # Type checking

# Clean
rm -rf .next         # Delete Next.js cache
rm -rf node_modules  # Delete dependencies (then npm install)
```

## Adding a New Component

1. Create file in `src/components/MyComponent.tsx`
2. Write component with TypeScript types
3. Import in the file where you need it
4. Use it

Example:

```tsx
// src/components/MyComponent.tsx
interface MyComponentProps {
  title: string;
}

export function MyComponent({ title }: MyComponentProps) {
  return <div className="p-4">{title}</div>;
}
```

## Making API Calls

**Option 1: Inside a component** (easiest for now)

```tsx
"use client"; // Mark as client component

import { apiClient } from "@/lib/api";
import { useEffect, useState } from "react";

export function MyData() {
  const [data, setData] = useState(null);

  useEffect(() => {
    apiClient
      .get("/dashboards/cell/123")
      .then((res) => setData(res.data))
      .catch((err) => console.error(err));
  }, []);

  return <div>{JSON.stringify(data)}</div>;
}
```

**Option 2: Create a service** (for Phase 2)

```tsx
// src/services/dashboardService.ts
import { apiClient } from "@/lib/api";

export const dashboardService = {
  getCell: (id: string) => apiClient.get(`/dashboards/cell/${id}`),
  getZone: (id: string) => apiClient.get(`/dashboards/zone/${id}`),
};
```

## Debugging Tips

### Check if token is saved

Open browser DevTools (F12) → Application → Local Storage:

```
auth_token: eyJhbGciOiJIUzI1NiI...
user: {"id":"123","name":"John","role":"cell_leader"}
```

### Check API requests

DevTools → Network tab → Look for requests to your backend:

```
POST http://localhost:8000/auth/login
Response: {"access_token":"...", "user": {...}}
```

### Check environment variable

Browser Console (F12):

```javascript
console.log(process.env.NEXT_PUBLIC_API_URL);
// Should print: http://localhost:8000
```

## Common Issues & Fixes

### "Module not found '@/components/Button'"

- Check file path is correct
- Make sure file exists at `src/components/Button.tsx`
- Restart VS Code's TypeScript server (Ctrl+Shift+P → TypeScript: Restart)

### Styling not showing

- Clear `.next` folder: `rm -rf .next`
- Restart: `npm run dev`
- Check class names match Tailwind config

### Login not working

- Is FastAPI running? (`python main.py`)
- Is `NEXT_PUBLIC_API_URL` correct?
- Check backend logs for errors
- In browser Network tab, see what error FastAPI returned

### Token not persisting on reload

- Check localStorage in DevTools
- Check if your browser allows localStorage (not in incognito)
- Check AuthContext `useEffect` is running

## Phase 2 Preview

Once you're comfortable with Phase 1, Phase 2 will add:

```tsx
// Example: Cell Dashboard Page
// src/app/(dashboard)/cell-leader/page.tsx

"use client";

import { Header } from "@/components/Header";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

export default function CellDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    apiClient.get("/dashboards/cell/123").then((res) => setData(res.data));
  }, []);

  return (
    <>
      <Header pageTitle="Cell Dashboard" />
      {/* Dashboard content goes here */}
    </>
  );
}
```

## Need Help?

1. **Read the comments** in each file - they explain the "why"
2. **Check README.md** for more detailed explanations
3. **Look at examples** - components show patterns you can copy
4. **Google errors** - 90% of issues have Stack Overflow answers
5. **Ask in communities** - r/nextjs, Next.js Discord, etc.

---

**You're ready!** Run `npm run dev` and start exploring the code. 🚀
