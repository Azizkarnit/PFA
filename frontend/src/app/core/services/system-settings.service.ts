import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface SystemSettings {
  code_expiration: number;
  max_signin_attempts: number;
  lock_duration: number;
  password_only_duration: number;
  default_language: string;
  email_provider: string;
}

@Injectable({
  providedIn: 'root'
})
export class SystemSettingsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/system-settings`;

  getSettings(): Observable<SystemSettings> {
    return this.http.get<SystemSettings>(this.apiUrl);
  }

  updateSettings(settings: SystemSettings): Observable<SystemSettings> {
    return this.http.put<SystemSettings>(this.apiUrl, settings);
  }
}
