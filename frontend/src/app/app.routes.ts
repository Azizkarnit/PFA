import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

const SUPERADMIN_ROLES = ['SYSTEM_ADMINISTRATOR', 'ACCOUNT_MANAGER'];
const ALL_ADMIN_ROLES = ['SYSTEM_ADMINISTRATOR', 'ACCOUNT_MANAGER', 'SURVEY_ADMINISTRATOR'];
const CONTACT_ROLES = ['COMPANY_CONTACT'];

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'otp',
    loadComponent: () =>
      import('./features/auth/otp-verification/otp-verification.component').then(m => m.OTPVerificationComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () =>
      import('./features/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    path: 'reset-password',
    loadComponent: () =>
      import('./features/auth/reset-password/reset-password.component').then(m => m.ResetPasswordComponent)
  },
  {
    path: 'change-password',
    loadComponent: () =>
      import('./features/auth/change-password/change-password.component').then(m => m.ChangePasswordComponent),
    canActivate: [authGuard]
  },
  {
    path: 'portal',
    loadComponent: () => import('./core/layouts/company-contact-layout/company-contact-layout').then(m => m.CompanyContactLayout),
    canActivate: [authGuard, roleGuard(CONTACT_ROLES)],
    children: [
      {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full'
      },
      {
        path: 'home',
        loadComponent: () => import('./features/company-contact/contact-home/contact-home').then(m => m.ContactHome)
      },
      {
        path: 'survey/:id',
        loadComponent: () => import('./features/company-contact/survey-detail/survey-detail').then(m => m.SurveyDetail)
      },
      {
        path: 'results',
        loadComponent: () => import('./features/company-contact/results/results').then(m => m.Results)
      },
      {
        path: 'my-surveys',
        loadComponent: () => import('./features/company-contact/my-surveys/my-surveys').then(m => m.MySurveys)
      },
      {
        path: 'profile',
        loadComponent: () => import('./features/company-contact/my-profile/my-profile').then(m => m.MyProfile)
      },
      {
        path: 'change-password',
        loadComponent: () => import('./features/company-contact/change-password/change-password').then(m => m.ChangePassword)
      }
    ]
  },
  {
    path: 'admin',
    loadComponent: () => import('./core/layouts/admin-layout/admin-layout').then(m => m.AdminLayout),
    canActivate: [authGuard, roleGuard(ALL_ADMIN_ROLES)],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        // All authenticated admin roles can see the dashboard
        path: 'dashboard',
        loadComponent: () => import('./features/superadmin/dashboard/dashboard').then(m => m.Dashboard),
        canActivate: [authGuard]
      },
      {
        // Only superadmin roles can manage administrators
        path: 'administrators',
        loadComponent: () => import('./features/superadmin/administrators/administrators').then(m => m.Administrators),
        canActivate: [roleGuard(SUPERADMIN_ROLES)]
      },
      {
        // System Administrators and Account Managers can view/manage locked accounts
        path: 'locked-accounts',
        loadComponent: () => import('./features/superadmin/locked-accounts/locked-accounts').then(m => m.LockedAccounts),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR', 'ACCOUNT_MANAGER'])]
      },
      {
        // All admin roles can view companies
        path: 'companies',
        loadComponent: () => import('./features/superadmin/companies/companies').then(m => m.Companies),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        // All admin roles can view contacts
        path: 'contacts',
        loadComponent: () => import('./features/superadmin/contacts/contacts').then(m => m.Contacts),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        // All admin roles can view surveys
        path: 'surveys',
        loadComponent: () => import('./features/superadmin/surveys/surveys').then(m => m.Surveys),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        path: 'create-survey',
        loadComponent: () => import('./features/superadmin/create-survey/create-survey').then(m => m.CreateSurvey),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        path: 'surveys/:id',
        loadComponent: () => import('./features/superadmin/survey-detail/survey-detail').then(m => m.SurveyDetail),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        // Only superadmin roles can read audit logs
        path: 'audit-logs',
        loadComponent: () => import('./features/superadmin/audit-logs/audit-logs').then(m => m.AuditLogs),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR'])]
      },
      {
        path: 'add-administrator',
        loadComponent: () => import('./features/superadmin/add-administrator/add-administrator').then(m => m.AddAdministrator),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR'])]
      },
      {
        path: 'add-company',
        loadComponent: () => import('./features/superadmin/add-company/add-company').then(m => m.AddCompany),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR'])]
      },
      {
        path: 'import-company',
        loadComponent: () => import('./features/superadmin/import-company/import-company').then(m => m.ImportCompany),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR'])]
      },
      {
        path: 'add-contact',
        loadComponent: () => import('./features/superadmin/add-contact/add-contact').then(m => m.AddContact),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        path: 'create-survey',
        loadComponent: () => import('./features/superadmin/create-survey/create-survey').then(m => m.CreateSurvey),
        canActivate: [roleGuard(ALL_ADMIN_ROLES)]
      },
      {
        // Only superadmin roles can change system-wide security settings
        path: 'system-settings',
        loadComponent: () => import('./features/superadmin/system-settings/system-settings').then(m => m.SystemSettings),
        canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR'])]
      },
      {
        path: 'profile',
        loadComponent: () => import('./features/profile/profile').then(m => m.ProfileComponent),
        canActivate: [authGuard]
      },
      {
        path: '**',
        redirectTo: 'dashboard'
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'login'
  }
];
