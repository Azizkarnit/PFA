import { HttpClient, HttpBackend } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

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
  first_name?: string;
  last_name?: string;
  first_login?: boolean;
  email_sent?: boolean;
  preferred_language?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  first_login: boolean;
  preferred_language: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly API = environment.apiUrl;
  private readonly TOKEN_KEY = 'ins_access_token';
  public readonly USER_KEY = 'ins_user';

  private http = inject(HttpClient);
  private httpBackend = inject(HttpBackend);
  private rawHttp = new HttpClient(this.httpBackend);
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
            first_name: res.first_name,
            last_name: res.last_name,
            first_login: res.first_login,
            preferred_language: res.preferred_language || 'fr'
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
            first_name: res.first_name,
            last_name: res.last_name,
            first_login: res.first_login,
            preferred_language: res.preferred_language || 'fr'
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
    // Revoke token server-side (blacklists the JWT jti in Redis)
    const token = this.getToken();
    if (token) {
      this.rawHttp.post(`${this.API}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      }).subscribe({
        error: () => { /* ignore network errors */ }
      });
    }
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

  updatePreferredLanguage(lang: string): Observable<any> {
    return this.http.put(`${this.API}/auth/me/language`, { preferred_language: lang }).pipe(
      tap(() => {
        const user = this.getCurrentUser();
        if (user) {
          user.preferred_language = lang;
          localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        }
      })
    );
  }

  getMe(): Observable<any> {
    return this.http.get(`${this.API}/auth/me`);
  }

  updateProfile(data: { first_name?: string, last_name?: string, phone_number?: string, preferred_language?: string }): Observable<any> {
    return this.http.put(`${this.API}/auth/me`, data);
  }

  updateProfilePassword(data: { current_password: string, new_password: string }): Observable<any> {
    return this.http.put(`${this.API}/auth/me/password`, data);
  }
}
