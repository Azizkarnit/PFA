import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PortalService, PortalSurveySummary } from '../../../core/services/portal.service';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-my-surveys',
  standalone: true,
  imports: [CommonModule, DatePipe, TranslatePipe, RouterLink],
  templateUrl: './my-surveys.html',
})
export class MySurveys implements OnInit {
  private portalService = inject(PortalService);

  isLoading = true;
  error: string | null = null;
  surveys: PortalSurveySummary[] = [];

  ngOnInit(): void {
    this.portalService.getSurveys().subscribe({
      next: data => {
        this.surveys = data;
        this.isLoading = false;
      },
      error: err => {
        console.error('Error loading surveys:', err);
        this.error = 'Failed to load surveys.';
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

  getActionIcon(status: string): string {
    switch (status) {
      case 'IN_PROGRESS': return 'edit_document';
      case 'COMPLETED': return 'check_circle';
      default: return 'play_arrow';
    }
  }

  getActionLabel(status: string): string {
    switch (status) {
      case 'IN_PROGRESS': return 'Continue';
      case 'COMPLETED': return 'View Details';
      default: return 'Start Survey';
    }
  }

  openSurveyLink(survey: PortalSurveySummary): void {
    if (!survey.passage_id) {
      console.error('Passage ID not available');
      return;
    }
    this.portalService.getSurveyLink(survey.passage_id).subscribe({
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

  downloadPdf(survey: PortalSurveySummary): void {
    if (survey.questionnaire_pdf_path) {
      const filename = survey.questionnaire_pdf_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/questionnaire/${filename}`, '_blank');
    }
  }
}
