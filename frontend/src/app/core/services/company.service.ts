import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Sector {
  id: number;
  name: string;
  code: string;
}

export interface Activity {
  id: number;
  name: string;
  code: string;
}

export interface Company {
  id: number;
  identifier: string;
  company_name: string;
  tax_number: string | null;
  address: string | null;
  governorate: string | null;
  postal_code: string | null;
  phone: string | null;
  email: string | null;
  status: string;
  sector: Sector;
  activity: Activity;
  contacts_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedCompanies {
  total_count: number;
  items: Company[];
}

@Injectable({
  providedIn: 'root'
})
export class CompanyService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/companies`;

  getCompanies(skip: number = 0, limit: number = 10, search?: string, sector?: number, activity?: number, governorate?: string, status?: string): Observable<PaginatedCompanies> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (search) params = params.set('search', search);
    if (sector) params = params.set('sector_id', sector.toString());
    if (activity) params = params.set('activity_id', activity.toString());
    if (governorate) params = params.set('governorate', governorate);
    if (status) params = params.set('status', status);

    return this.http.get<PaginatedCompanies>(this.apiUrl, { params });
  }

  getSectors(): Observable<Sector[]> {
    return this.http.get<Sector[]>(`${this.apiUrl}/sectors`);
  }

  getActivities(): Observable<Activity[]> {
    return this.http.get<Activity[]>(`${this.apiUrl}/activities`);
  }

  createCompany(data: any): Observable<Company> {
    return this.http.post<Company>(this.apiUrl, data);
  }

  updateCompany(id: number, data: Partial<Company>): Observable<Company> {
    return this.http.patch<Company>(`${this.apiUrl}/${id}`, data);
  }

  updateCompanyStatus(id: number, status: string): Observable<Company> {
    let params = new HttpParams().set('status', status);
    return this.http.patch<Company>(`${this.apiUrl}/${id}/status`, null, { params });
  }

  previewImport(file: File): Observable<{ session_id: string, status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<{ session_id: string, status: string }>(`${this.apiUrl}/import/preview`, formData);
  }

  checkImportSession(sessionId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/import/session/${sessionId}`);
  }

  cancelImportSession(sessionId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/import/session/${sessionId}`);
  }

  getImportStaging(sessionId: string, page: number = 1, pageSize: number = 10, status: string = 'all'): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    
    if (status) {
      params = params.set('status', status);
    }
    
    return this.http.get<any>(`${this.apiUrl}/import/staging/${sessionId}`, { params });
  }

  updateStagingRow(sessionId: string, rowNumber: number, data: any): Observable<any> {
    return this.http.patch<any>(`${this.apiUrl}/import/staging/${sessionId}/${rowNumber}`, data);
  }

  downloadTemplate(): void {
    this.http.get(`${this.apiUrl}/import/template`, { responseType: 'blob' }).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'companies_import_template.xlsx';
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  confirmImport(sessionId: string): Observable<ImportConfirmResponse> {
    return this.http.post<ImportConfirmResponse>(`${this.apiUrl}/import/confirm`, { session_id: sessionId });
  }
}

export interface ImportRowResult {
  row_number: number;
  status: 'valid' | 'error' | 'warning';
  errors: string[];
  warnings: string[];
  data: any;
}

export interface ImportPreviewResponse {
  total_rows: number;
  valid_count: number;
  error_count: number;
  warning_count: number;
  rows: ImportRowResult[];
}

export interface ImportConfirmResponse {
  imported: number;
  skipped: number;
  errors: string[];
}
