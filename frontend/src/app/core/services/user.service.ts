import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface UserAdmin {
  id: number;
  name: string;
  first_name?: string;
  last_name?: string;
  email: string;
  phone?: string;
  status: string;
  role_name: string;
  role_code?: string;
  last_login?: string;
}

export interface PaginatedUsers {
  total_count: number;
  items: UserAdmin[];
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/users`;

  getUsers(skip: number = 0, limit: number = 10, search?: string, status?: string, role?: string): Observable<PaginatedUsers> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (search) {
      params = params.set('search', search);
    }
    if (status) {
      params = params.set('status', status);
    }
    if (role) {
      params = params.set('role', role);
    }

    return this.http.get<PaginatedUsers>(this.apiUrl, { params });
  }

  createUser(payload: { first_name: string; last_name: string; email: string; phone?: string; role_id: number }): Observable<UserAdmin> {
    return this.http.post<UserAdmin>(this.apiUrl, payload);
  }

  updateUser(userId: number, payload: { first_name: string; last_name: string; phone?: string; role_id: number }): Observable<UserAdmin> {
    return this.http.put<UserAdmin>(`${this.apiUrl}/${userId}`, payload);
  }

  updateUserStatus(userId: number, status: string): Observable<{ message: string }> {
    return this.http.patch<{ message: string }>(`${this.apiUrl}/${userId}/status`, { status });
  }

  getRoles(): Observable<{ id: number; name: string; description: string }[]> {
    return this.http.get<{ id: number; name: string; description: string }[]>(`${this.apiUrl}/roles`);
  }

  getLockedAccounts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/locked/accounts`);
  }

  unlockAccount(userId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/${userId}/unlock`, {});
  }
}
