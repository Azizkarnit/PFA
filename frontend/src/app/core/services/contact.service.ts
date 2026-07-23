import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Contact {
  id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string | null;
  position: string | null;
  is_primary_contact: boolean;
  company_id: number;
  company_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedContactResponse {
  total_count: number;
  items: Contact[];
}

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  getContacts(skip: number = 0, limit: number = 10, search?: string, companyId?: number, statusFilter?: string): Observable<PaginatedContactResponse> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (search) params = params.set('search', search);
    if (companyId) params = params.set('company_id', companyId.toString());
    if (statusFilter && statusFilter !== 'ALL') params = params.set('status_filter', statusFilter);

    return this.http.get<PaginatedContactResponse>(`${this.apiUrl}/contacts`, { params });
  }

  createContact(data: any): Observable<Contact> {
    return this.http.post<Contact>(`${this.apiUrl}/contacts`, data);
  }

  updateContact(id: number, data: any): Observable<Contact> {
    return this.http.put<Contact>(`${this.apiUrl}/contacts/${id}`, data);
  }

  toggleStatus(id: number): Observable<{message: string, status: string}> {
    return this.http.patch<{message: string, status: string}>(`${this.apiUrl}/contacts/${id}/status`, {});
  }
}
