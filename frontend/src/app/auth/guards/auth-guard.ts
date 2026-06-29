import { Injectable, inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');
  
  if (token) {
    return true;
  }
  
  // Not logged in so redirect to login page
  router.navigate(['/auth/login'], { queryParams: { returnUrl: state.url }});
  return false;
};
