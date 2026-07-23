import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { PortalService, PortalResultFile } from '../../../core/services/portal.service';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe, FormsModule, TranslatePipe],
  templateUrl: './results.html',
  styles: ``,
})
export class Results implements OnInit {
  private portalService = inject(PortalService);

  isLoading = true;
  error: string | null = null;
  
  allResults: PortalResultFile[] = [];
  filteredResults: PortalResultFile[] = [];

  // Filters
  searchQuery: string = '';
  dateSort: 'desc' | 'asc' = 'desc';
  typeFilter: 'ALL' | 'PDF' | 'EXCEL' = 'ALL';

  ngOnInit(): void {
    this.portalService.getAllResults().subscribe({
      next: data => {
        this.allResults = data;
        this.applyFilters();
        this.isLoading = false;
      },
      error: err => {
        console.error('Error loading results:', err);
        this.error = 'Failed to load results.';
        this.isLoading = false;
      }
    });
  }

  applyFilters(): void {
    let temp = [...this.allResults];

    // Text search
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      temp = temp.filter(r => 
        r.survey_name.toLowerCase().includes(q) || 
        r.file_name.toLowerCase().includes(q)
      );
    }

    // Type filter
    if (this.typeFilter !== 'ALL') {
      temp = temp.filter(r => r.file_type === this.typeFilter);
    }

    // Date sort
    temp.sort((a, b) => {
      const timeA = new Date(a.uploaded_at).getTime();
      const timeB = new Date(b.uploaded_at).getTime();
      return this.dateSort === 'desc' ? timeB - timeA : timeA - timeB;
    });

    this.filteredResults = temp;
  }

  downloadResult(result: PortalResultFile): void {
    if (result.file_path) {
      const filename = result.file_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/result/${filename}`, '_blank');
    }
  }
}
