import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface LockedAccount {
  id: number;
  name: string;
  email: string;
  locked_since: string;
}

export interface RecentContact {
  id: number;
  name: string;
  email: string;
  company_name?: string;
  position?: string;
  status: string;
  created_at: string;
}

export interface RecentActivity {
  id: number;
  type: string;
  description: string;
  timestamp: string;
}

export interface RoleDistribution {
  role_name: string;
  count: number;
  percentage: number;
  color?: string;
}

export interface SectorDistribution {
  sector_name: string;
  count: number;
}

export interface StatusDistribution {
  status: string;
  count: number;
}

export interface GrowthPoint {
  month: string;
  count: number;
}

export interface RecentSurvey {
  id: number;
  code: string;
  name: string;
  periodicity: string;
  status: string;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  active_companies: number;
  locked_accounts_count: number;
  total_surveys: number;
  locked_accounts: LockedAccount[];
  recent_activities: RecentActivity[];
  role_distribution: RoleDistribution[];
  companies_by_sector: SectorDistribution[];
  companies_by_status: StatusDistribution[];
  companies_growth: GrowthPoint[];
  surveys_growth: GrowthPoint[];
  total_contacts?: number;
  contacts_growth: GrowthPoint[];
  recent_contacts: RecentContact[];
  // Survey Admin specific
  my_surveys_count?: number;
  my_active_passages_count?: number;
  my_total_passages_count?: number;
  my_monitored_companies_count?: number;
  my_recent_surveys?: RecentSurvey[];
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/dashboard`;

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.apiUrl}/stats`);
  }
}
