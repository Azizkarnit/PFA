import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AuditLogUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  user: AuditLogUser;
  action: string;
  entity_type: string;
  entity_id?: number;
  old_values?: any;
  new_values?: any;
  ip_address?: string;
  created_at: string;
}

export interface PaginatedAuditLogResponse {
  items: AuditLog[];
  total_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class AuditLogService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/audit-logs`;

  getAuditLogs(
    skip: number = 0,
    limit: number = 10,
    search?: string,
    action?: string,
    dateFrom?: string,
    dateTo?: string
  ): Observable<PaginatedAuditLogResponse> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (search) params = params.set('search', search);
    if (action) params = params.set('action', action);
    if (dateFrom) params = params.set('date_from', dateFrom);
    if (dateTo) params = params.set('date_to', dateTo);

    return this.http.get<PaginatedAuditLogResponse>(this.apiUrl, { params });
  }

  exportAuditLogs(
    search?: string,
    action?: string,
    dateFrom?: string,
    dateTo?: string
  ): Observable<{ task_id: string }> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (action) params = params.set('action', action);
    if (dateFrom) params = params.set('date_from', dateFrom);
    if (dateTo) params = params.set('date_to', dateTo);

    return this.http.post<{ task_id: string }>(`${this.apiUrl}/export`, null, {
      params
    });
  }

  checkExportStatus(taskId: string): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.apiUrl}/export/status/${taskId}`);
  }

  downloadExportFile(taskId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/export/download/${taskId}`, { responseType: 'blob' });
  }
}
