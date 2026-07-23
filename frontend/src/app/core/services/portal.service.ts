import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface PortalSurveySummary {
  id: number;
  code: string;
  name: string;
  periodicity: string | null;
  status: string;
  visit_status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  passage_id: number | null;
  passage_year: number | null;
  passage_number: number | null;
  closing_date: string | null;
  questionnaire_pdf_path: string | null;
}

export interface PortalResultFile {
  id: number;
  survey_id: number;
  survey_name: string;
  file_name: string;
  file_path: string;
  file_type: 'PDF' | 'EXCEL';
  uploaded_at: string;
}


export interface PortalProfile {
  first_name: string;
  last_name: string;
  position: string | null;
  company_name: string;
  company_identifier: string;
  sector_name: string | null;
  email: string;
  preferred_language: string;
}

export interface PortalProfileUpdate {
  first_name: string;
  last_name: string;
  position: string | null;
  preferred_language: string;
}

export interface PortalHomeData {
  first_name: string;
  last_name: string;
  company_name: string;
  position: string | null;
  assigned_surveys_count: number;
  pending_actions_count: number;
  surveys: PortalSurveySummary[];
  results: PortalResultFile[];
}

@Injectable({ providedIn: 'root' })
export class PortalService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/portal`;

  getHomeData(): Observable<PortalHomeData> {
    return this.http.get<PortalHomeData>(`${this.apiUrl}/home`);
  }


  getProfile(): Observable<PortalProfile> {
    return this.http.get<PortalProfile>(`${this.apiUrl}/profile`);
  }

  updateProfile(data: PortalProfileUpdate): Observable<PortalProfile> {
    return this.http.put<PortalProfile>(`${this.apiUrl}/profile`, data);
  }

  getSurveys(): Observable<PortalSurveySummary[]> {
    return this.http.get<PortalSurveySummary[]>(`${this.apiUrl}/surveys`);
  }

  getAllResults(): Observable<PortalResultFile[]> {
    return this.http.get<PortalResultFile[]>(`${this.apiUrl}/results`);
  }

  getSurveyLink(passageId: number): Observable<{ url: string }> {
    return this.http.get<{ url: string }>(`${this.apiUrl}/survey-link?passage_id=${passageId}`);
  }
}
