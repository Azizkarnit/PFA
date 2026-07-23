import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PortalService, PortalHomeData, PortalSurveySummary, PortalResultFile } from '../../../core/services/portal.service';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-contact-home',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe, TranslatePipe],
  templateUrl: './contact-home.html',
})
export class ContactHome implements OnInit {
  private portalService = inject(PortalService);

  isLoading = true;
  error: string | null = null;

  homeData: PortalHomeData | null = null;

  ngOnInit(): void {
    this.portalService.getHomeData().subscribe({
      next: data => {
        this.homeData = data;
        this.isLoading = false;
      },
      error: err => {
        console.error('Error loading portal home:', err);
        this.error = 'Failed to load dashboard data.';
        this.isLoading = false;
      }
    });
  }

  get surveys(): PortalSurveySummary[] {
    return this.homeData?.surveys ?? [];
  }

  get results(): PortalResultFile[] {
    return this.homeData?.results ?? [];
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
      case 'IN_PROGRESS': return 'Open questionnaire';
      case 'COMPLETED': return 'View submission';
      default: return 'Start questionnaire';
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
      // Extract basename in case the path contains directory separators (from dummy data)
      const filename = survey.questionnaire_pdf_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/questionnaire/${filename}`, '_blank');
    }
  }

  downloadResult(result: PortalResultFile): void {
    if (result.file_path) {
      const filename = result.file_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/result/${filename}`, '_blank');
    }
  }

  getFileIcon(fileType: string): string {
    return fileType === 'PDF' ? 'picture_as_pdf' : 'table_view';
  }

  getFileTypeStyle(fileType: string): { [key: string]: string } {
    if (fileType === 'PDF') {
      return { 'background-color': '#ffdad6', 'color': '#93000a' };
    }
    return { 'background-color': 'rgba(30, 142, 90, 0.1)', 'color': '#1E8E5A' };
  }
}
