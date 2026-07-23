# INS Platform Frontend — Angular 21 Single Page Application

Modern administrative portal and survey management frontend built with **Angular 21**, **Angular Material**, **RxJS**, and **ApexCharts**.

---

## 🏗️ Tech Stack

- **Framework:** Angular 21 (Standalone Components)
- **UI & Layout:** Angular Material + Modern Vanilla CSS design system
- **State & Async:** RxJS Signals & Observables
- **Data Visualization:** ApexCharts / Ng-ApexCharts
- **Internationalization:** `@ngx-translate` (French / English / Arabic ready)
- **HTTP Client:** Native Angular HttpClient with JWT Interceptors

---

## 📁 Folder Structure

```
frontend/src/
├── app/
│   ├── core/
│   │   ├── guards/         # AuthGuard, RoleGuard (RBAC protection)
│   │   ├── services/       # Feature API services (Auth, Company, Survey, Audit, WebSocket)
│   │   └── layouts/        # Dashboard layout shells
│   ├── features/
│   │   ├── auth/           # Login, OTP verification, Password Reset
│   │   ├── superadmin/     # System Admin dashboards, Company management, Imports
│   │   ├── company-contact/# Contact survey consultation portal
│   │   └── profile/        # User profile settings
│   └── shared/
│       └── components/     # Reusable components (Sidebar, Topbar, Modals)
├── assets/                 # Logos, static icons, i18n JSON files
└── environments/           # Development & Production API endpoints
```

---

## 🚀 Quick Start

### 1. Installation
Ensure Node.js 20+ is installed on your system.
```bash
npm install
```

### 2. Development Server
Start the Angular local development server:
```bash
npm start
```
Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

### 3. Build for Production
To compile the production build:
```bash
npm run build
```
The build artifacts will be stored in the `dist/frontend` directory.

---

## 🔐 Role-Based Access Control (RBAC)

The application enforces front-end route protection via Angular Guards:
- **`AuthGuard`**: Restricts unauthorized access to protected paths.
- **`RoleGuard`**: Validates role permissions for:
  - `SYSTEM_ADMINISTRATOR`: Full platform setup & management.
  - `ACCOUNT_MANAGER`: Company & contact directory administration.
  - `SURVEY_MANAGER`: Survey campaign lifecycle & passage assignments.
  - `COMPANY_CONTACT`: Company survey consultation portal.
