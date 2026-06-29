import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { OtpVerify } from './pages/otp-verify/otp-verify';
import { ForgotPassword } from './pages/forgot-password/forgot-password';
import { ResetPassword } from './pages/reset-password/reset-password';
import { ChangePassword } from './pages/change-password/change-password';

export const authRoutes: Routes = [
  { path: 'login', component: Login },
  { path: 'verify-otp', component: OtpVerify },
  { path: 'forgot-password', component: ForgotPassword },
  { path: 'reset-password', component: ResetPassword },
  { path: 'change-password', component: ChangePassword },
  { path: '', redirectTo: 'login', pathMatch: 'full' }
];
