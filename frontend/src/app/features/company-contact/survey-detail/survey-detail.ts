import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PortalService, PortalSurveySummary } from '../../../core/services/portal.service';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-survey-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe, TranslatePipe],
  templateUrl: './survey-detail.html',
  styles: ``,
})
export class SurveyDetail implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private portalService = inject(PortalService);

  surveyId!: number;
  survey: PortalSurveySummary | null = null;
  isLoading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.surveyId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadSurveyDetails();
  }

  loadSurveyDetails(): void {
    this.portalService.getSurveys().subscribe({
      next: list => {
        const found = list.find(s => s.id === this.surveyId);
        if (found) {
          this.survey = found;
        } else {
          this.error = 'Survey not found or you do not have access to it.';
        }
        this.isLoading = false;
      },
      error: err => {
        console.error('Error loading survey details:', err);
        this.error = 'Failed to load survey details.';
        this.isLoading = false;
      }
    });
  }

  getVisitStatusLabel(status: string): string {
    switch (status) {
      case 'IN_PROGRESS': return 'In progress';
      case 'COMPLETED': return 'Completed';
      default: return 'Not started';
    }
  }

  getVisitStatusStyle(status: string): { [key: string]: string } {
    switch (status) {
      case 'IN_PROGRESS':
        return { 'background-color': '#ffdcc6', 'color': '#7b3c00', 'border-color': 'rgba(217,138,0,0.2)' };
      case 'COMPLETED':
        return { 'background-color': '#d4edda', 'color': '#155724', 'border-color': 'rgba(21,87,36,0.2)' };
      default:
        return { 'background-color': '#d3e4ff', 'color': '#0b4f8a', 'border-color': 'rgba(11,79,138,0.2)' };
    }
  }

  openSurveyLink(): void {
    if (!this.survey || !this.survey.passage_id) return;
    this.portalService.getSurveyLink(this.survey.passage_id).subscribe({
      next: res => {
        if (res.url) {
          window.open(res.url, '_blank');
        }
      },
      error: err => {
        console.error('Error retrieving external survey link:', err);
      }
    });
  }

  downloadPdf(): void {
    if (this.survey && this.survey.questionnaire_pdf_path) {
      const filename = this.survey.questionnaire_pdf_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/questionnaire/${filename}`, '_blank');
    }
  }
}
