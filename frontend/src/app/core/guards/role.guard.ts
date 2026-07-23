import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Factory that creates a role-based guard.
 * Usage: canActivate: [roleGuard(['SYSTEM_ADMINISTRATOR', 'ACCOUNT_MANAGER'])]
 */
export const roleGuard = (allowedRoles: string[]): CanActivateFn => {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (!auth.isLoggedIn()) {
      router.navigate(['/login']);
      return false;
    }

    const user = auth.getCurrentUser();
    if (!user || !allowedRoles.includes(user.role)) {
      // Redirect to their default page rather than exposing a 403 route
      if (user?.role === 'COMPANY_CONTACT') {
        router.navigate(['/portal/home']);
      } else if (user) {
        router.navigate(['/admin/dashboard']);
      } else {
        router.navigate(['/login']);
      }
      return false;
    }

    return true;
  };
};
