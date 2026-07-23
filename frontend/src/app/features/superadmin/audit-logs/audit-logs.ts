import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuditLogService, AuditLog } from '../../../core/services/audit-log.service';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './audit-logs.html',
  styleUrl: './audit-logs.css'
})
export class AuditLogs implements OnInit, OnDestroy {
  private auditLogService = inject(AuditLogService);

  Math = Math;
  logs: AuditLog[] = [];
  totalCount = 0;
  
  // Pagination
  currentPage = 1;
  pageSize = 15;
  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalCount / this.pageSize));
  }

  get startIndex(): number {
    return this.totalCount === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalCount);
  }

  // Filters
  searchQuery = '';
  selectedAction = '';
  dateFrom = '';
  dateTo = '';

  isExporting = false;

  // Sidebar details
  selectedLog: AuditLog | null = null;

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    const skip = (this.currentPage - 1) * this.pageSize;
    
    // API expects dates in ISO format or similar, HTML date inputs are YYYY-MM-DD
    const fromStr = this.dateFrom ? `${this.dateFrom}T00:00:00` : undefined;
    const toStr = this.dateTo ? `${this.dateTo}T23:59:59` : undefined;

    this.auditLogService.getAuditLogs(
      skip, this.pageSize,
      this.searchQuery || undefined,
      this.selectedAction || undefined,
      fromStr, toStr
    ).subscribe({
      next: (res) => {
        this.logs = res.items;
        this.totalCount = res.total_count;
      },
      error: (err) => console.error('Error loading audit logs', err)
    });
  }

  onFilterChange() {
    this.currentPage = 1;
    this.loadLogs();
  }

  clearFilters(event?: Event) {
    if (event) {
      event.preventDefault();
    }
    this.searchQuery = '';
    this.selectedAction = '';
    this.dateFrom = '';
    this.dateTo = '';
    this.currentPage = 1;
    this.loadLogs();
  }

  changePage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadLogs();
    }
  }

  exportPollingInterval: any;

  exportToCsv() {
    this.isExporting = true;
    
    const fromStr = this.dateFrom ? `${this.dateFrom}T00:00:00` : undefined;
    const toStr = this.dateTo ? `${this.dateTo}T23:59:59` : undefined;

    this.auditLogService.exportAuditLogs(
      this.searchQuery || undefined,
      this.selectedAction || undefined,
      fromStr, toStr
    ).subscribe({
      next: (res) => {
        const taskId = res.task_id;
        this.exportPollingInterval = setInterval(() => {
          this.auditLogService.checkExportStatus(taskId).subscribe((statusRes) => {
            if (statusRes.status === 'SUCCESS') {
              clearInterval(this.exportPollingInterval);
              this.auditLogService.downloadExportFile(taskId).subscribe(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `audit_logs_${new Date().getTime()}.xlsx`;
                a.click();
                window.URL.revokeObjectURL(url);
                this.isExporting = false;
              });
            } else if (statusRes.status === 'FAILURE') {
               clearInterval(this.exportPollingInterval);
               this.isExporting = false;
               alert('Failed to export audit logs.');
            }
          });
        }, 2000);
      },
      error: (err) => {
        this.isExporting = false;
        console.error('Error starting export', err);
      }
    });
  }

  openDetails(log: AuditLog) {
    this.selectedLog = log;
  }

  closeSidebar() {
    this.selectedLog = null;
  }

  objectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  getActionBadgeClass(action: string): string {
    if (action.includes('Created')) return 'bg-success bg-opacity-10 text-success border-success';
    if (action.includes('Updated')) return 'bg-warning bg-opacity-10 text-warning border-warning';
    if (action.includes('Disabled')) return 'bg-danger bg-opacity-10 text-danger border-danger';
    if (action.includes('Enabled')) return 'bg-info bg-opacity-10 text-info border-info';
    if (action.includes('Unlocked')) return 'bg-primary bg-opacity-10 text-primary border-primary';
    if (action.includes('Login') || action === 'LOGIN') return 'bg-secondary bg-opacity-10 text-secondary border-secondary';
    return 'bg-light text-dark border-secondary';
  }

  ngOnDestroy() {
    if (this.exportPollingInterval) {
      clearInterval(this.exportPollingInterval);
    }
  }
}
