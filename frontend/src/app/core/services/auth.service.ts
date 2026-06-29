import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  require_otp: boolean;
  access_token?: string;
  token_type?: string;
  role?: string;
  user_id?: number;
  email?: string;
  first_login?: boolean;
  email_sent?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
  email: string;
  first_login: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly API = 'http://localhost:8000/api/v1';
  private readonly TOKEN_KEY = 'ins_access_token';
  private readonly USER_KEY = 'ins_user';

  private http = inject(HttpClient);
  private router = inject(Router);

  login(payload: LoginPayload): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.API}/auth/login`, payload).pipe(
      tap(res => {
        if (res.access_token) {
          localStorage.setItem(this.TOKEN_KEY, res.access_token);
          localStorage.setItem(this.USER_KEY, JSON.stringify({
            email: res.email,
            role: res.role,
            user_id: res.user_id,
            first_login: res.first_login
          }));
        }
      })
    );
  }

  verifyOtp(email: string, code: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.API}/auth/verify-otp`, { email, code }).pipe(
      tap(res => {
        if (res.access_token) {
          localStorage.setItem(this.TOKEN_KEY, res.access_token);
          localStorage.setItem(this.USER_KEY, JSON.stringify({
            email: res.email,
            role: res.role,
            user_id: res.user_id,
            first_login: res.first_login
          }));
        }
      })
    );
  }

  requestOtp(email: string): Observable<any> {
    return this.http.post(`${this.API}/auth/request-otp`, { email });
  }

  changePassword(new_password: string): Observable<any> {
    return this.http.post(
      `${this.API}/auth/change-password`,
      { new_password },
      { headers: { Authorization: `Bearer ${this.getToken()}` } }
    );
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${this.API}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, new_password: string): Observable<any> {
    return this.http.post(`${this.API}/auth/reset-password`, { token, new_password });
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  getCurrentUser(): any {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) : null;
  }
}
