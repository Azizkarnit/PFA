import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface AssignedAdmin { id: number; name: string; email: string; }

export interface Survey {
  id: number; code: string; name: string; description?: string;
  periodicity: string; status: string;
  assigned_admins: AssignedAdmin[];
  passage_count: number; last_passage_year?: number; last_passage_number?: number;
  created_by: number; created_at: string; updated_at: string;
}
export interface PaginatedSurveys { total_count: number; items: Survey[]; }

export interface SurveyCreate {
  code: string; name: string; description?: string;
  periodicity: string; assigned_admin_ids: number[]; status: string;
}
export interface SurveyUpdate {
  name?: string; description?: string; periodicity?: string;
  assigned_admin_ids?: number[]; status?: string;
}

// ── Passage ──────────────────────────────────────────────────────────────────
export interface Passage {
  id: number; survey_id: number; year: number; passage_number: number;
  opening_date: string; closing_date: string; status: string;
  company_count: number; created_at: string; updated_at: string;
}
export interface PaginatedPassages { total_count: number; items: Passage[]; }

export interface PassageCreate {
  year: number; passage_number: number; opening_date: string; closing_date: string;
}
export interface PassageUpdate {
  opening_date?: string; closing_date?: string; status?: string;
}

// ── Questionnaire ─────────────────────────────────────────────────────────────
export interface Questionnaire {
  id: number; passage_id: number;
  questionnaire_url?: string; questionnaire_pdf_path?: string;
  version: string; status: string; created_at: string;
}
export interface QuestionnaireCreate { questionnaire_url?: string; version?: string; }

// ── Sample ────────────────────────────────────────────────────────────────────
export interface SampleInfo {
  id: number;
  passage_id: number;
  total_companies: number;
  uploaded_by: number;
  uploader_name?: string;
  created_at: string;
  companies: {
    id: number;
    identifier: string;
    company_name: string;
    status: string;
  }[];
}

// ── Monitoring ────────────────────────────────────────────────────────────────
export interface MonitoringPassageStat {
  passage_id: number; passage_year: number; passage_number: number;
  passage_status: string; total_companies: number;
  not_started: number; in_progress: number; completed: number; completion_pct: number;
}
export interface SurveyMonitoring {
  survey_id: number; total_passages: number;
  total_companies_all_passages: number; passages: MonitoringPassageStat[];
}

// ── Results ───────────────────────────────────────────────────────────────────
export interface ResultFile {
  id: number; survey_id: number; sector_id: number; sector_name?: string;
  file_name: string; file_path: string; file_type: string;
  uploaded_by: number; uploader_name?: string; uploaded_at: string;
}

// ─── Service ──────────────────────────────────────────────────────────────────

@Injectable({ providedIn: 'root' })
export class SurveyService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/surveys`;

  // ── Lookups ────────────────────────────────────────────────────────────────
  getSurveyAdmins(): Observable<AssignedAdmin[]> {
    return this.http.get<AssignedAdmin[]>(`${this.apiUrl}/admins`);
  }

  getAssignedAdminsFilter(): Observable<AssignedAdmin[]> {
    return this.http.get<AssignedAdmin[]>(`${this.apiUrl}/assigned-admins-filter`);
  }

  // ── Surveys ────────────────────────────────────────────────────────────────
  getSurveys(skip = 0, limit = 10, search?: string, status?: string, periodicity?: string, assignedAdminId?: number): Observable<PaginatedSurveys> {
    let params = new HttpParams().set('skip', skip).set('limit', limit);
    if (search) params = params.set('search', search);
    if (status && status !== 'ALL') params = params.set('status', status);
    if (periodicity) params = params.set('periodicity', periodicity);
    if (assignedAdminId) params = params.set('assigned_admin_id', assignedAdminId);
    return this.http.get<PaginatedSurveys>(`${this.apiUrl}/`, { params });
  }
  getSurvey(id: number): Observable<Survey> {
    return this.http.get<Survey>(`${this.apiUrl}/${id}`);
  }
  createSurvey(data: SurveyCreate): Observable<Survey> {
    return this.http.post<Survey>(`${this.apiUrl}/`, data);
  }
  updateSurvey(id: number, data: SurveyUpdate): Observable<Survey> {
    return this.http.patch<Survey>(`${this.apiUrl}/${id}`, data);
  }
  updateSurveyStatus(id: number, newStatus: string): Observable<Survey> {
    return this.http.patch<Survey>(`${this.apiUrl}/${id}/status`, null, { params: { new_status: newStatus } });
  }
  checkCodeAvailable(code: string): Observable<{ available: boolean }> {
    return this.http.get<{ available: boolean }>(`${this.apiUrl}/check-code/${encodeURIComponent(code)}`);
  }

  // ── Passages ───────────────────────────────────────────────────────────────
  getPassages(surveyId: number, skip = 0, limit = 50): Observable<PaginatedPassages> {
    return this.http.get<PaginatedPassages>(`${this.apiUrl}/${surveyId}/passages`, { params: { skip, limit } });
  }
  createPassage(surveyId: number, data: PassageCreate): Observable<Passage> {
    return this.http.post<Passage>(`${this.apiUrl}/${surveyId}/passages`, data);
  }
  updatePassage(surveyId: number, passageId: number, data: PassageUpdate): Observable<Passage> {
    return this.http.patch<Passage>(`${this.apiUrl}/${surveyId}/passages/${passageId}`, data);
  }

  // ── Questionnaire ──────────────────────────────────────────────────────────
  getQuestionnaire(surveyId: number, passageId: number): Observable<Questionnaire | null> {
    return this.http.get<Questionnaire | null>(`${this.apiUrl}/${surveyId}/passages/${passageId}/questionnaire`);
  }
  upsertQuestionnaire(surveyId: number, passageId: number, data: QuestionnaireCreate): Observable<Questionnaire> {
    return this.http.post<Questionnaire>(`${this.apiUrl}/${surveyId}/passages/${passageId}/questionnaire`, data);
  }
  uploadQuestionnairePdf(surveyId: number, passageId: number, file: File): Observable<{ task_id: string }> {
    const fd = new FormData(); fd.append('file', file);
    return this.http.post<{ task_id: string }>(`${this.apiUrl}/${surveyId}/passages/${passageId}/questionnaire/pdf`, fd);
  }

  // ── Sample ─────────────────────────────────────────────────────────────────
  getSample(surveyId: number, passageId: number): Observable<SampleInfo | null> {
    return this.http.get<SampleInfo | null>(`${this.apiUrl}/${surveyId}/passages/${passageId}/sample`);
  }
  uploadSample(surveyId: number, passageId: number, file: File): Observable<{task_id: string}> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<{task_id: string}>(`${this.apiUrl}/${surveyId}/passages/${passageId}/sample`, formData);
  }
  downloadSampleTemplate(): void {
    this.http.get(`${this.apiUrl}/samples/template`, { responseType: 'blob' }).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'survey_sample_template.xlsx';
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => console.error('Error downloading template', err)
    });
  }

  // ── Monitoring ─────────────────────────────────────────────────────────────
  getMonitoring(surveyId: number): Observable<SurveyMonitoring> {
    return this.http.get<SurveyMonitoring>(`${this.apiUrl}/${surveyId}/monitoring`);
  }

  // ── Results ────────────────────────────────────────────────────────────────
  getResults(surveyId: number): Observable<ResultFile[]> {
    return this.http.get<{ items: ResultFile[] }>(`${this.apiUrl}/${surveyId}/results`).pipe(
      map(r => r.items)
    );
  }
  uploadResult(surveyId: number, sectorId: number, file: File): Observable<{ task_id: string }> {
    const fd = new FormData(); fd.append('file', file);
    return this.http.post<{ task_id: string }>(`${this.apiUrl}/${surveyId}/results`, fd, { params: { sector_id: sectorId } });
  }
  uploadResultWithProgress(surveyId: number, sectorId: number, file: File): Observable<any> {
    const fd = new FormData(); fd.append('file', file);
    return this.http.post(`${this.apiUrl}/${surveyId}/results`, fd, { 
      params: { sector_id: sectorId },
      reportProgress: true,
      observe: 'events'
    });
  }
  deleteResult(surveyId: number, resultId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${surveyId}/results/${resultId}`);
  }

  // ── Reports & Tasks ─────────────────────────────────────────────────────────
  generateReport(surveyId: number, format: 'excel' | 'pdf'): Observable<{ task_id: string }> {
    return this.http.post<{ task_id: string }>(`${this.apiUrl}/${surveyId}/reports/export`, null, { params: { format } });
  }
  
  getTaskStatus(taskId: string): Observable<{ task_id: string, status: string, result?: any, error?: string }> {
    // using the root environment.apiUrl for this if we want, or just this.apiUrl
    // actually the route is inside /surveys router so it's this.apiUrl/tasks/{taskId}
    return this.http.get<{ task_id: string, status: string, result?: any, error?: string }>(`${this.apiUrl}/tasks/${taskId}`);
  }
}
