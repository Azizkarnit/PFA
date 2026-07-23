import { LanguageService } from '../../../core/services/language.service';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { Component, inject, ElementRef, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import {
  CompanyService,
  ImportPreviewResponse,
  ImportRowResult,
  ImportConfirmResponse
} from '../../../core/services/company.service';

type Step = 'upload' | 'loading' | 'preview' | 'confirming' | 'done';

@Component({
  selector: 'app-import-company',
  imports: [CommonModule, RouterLink, FormsModule, TranslatePipe],
  templateUrl: './import-company.html',
  styleUrl: './import-company.css',
})
export class ImportCompany implements OnInit, OnDestroy {
  public langService = inject(LanguageService);
  private translate = inject(TranslateService);

  @ViewChild('fileInput') fileInputRef!: ElementRef<HTMLInputElement>;

  step: Step = 'upload';
  selectedFile: File | null = null;
  isDragOver = false;
  uploadError = '';
  isConfirming = false;

  previewData: any = null;
  confirmResult: ImportConfirmResponse | null = null;
  sessionId = '';
  pollingInterval: any;
  pagedRowsFromServer: ImportRowResult[] = [];
  totalRowsFromServer = 0;

  // Sectors & Activities
  sectors: any[] = [];
  activities: any[] = [];

  // Tunisian Governorates
  governorates = [
    'Ariana', 'Beja', 'Ben Arous', 'Bizerte', 'Gabes', 'Gafsa', 'Jendouba', 'Kairouan',
    'Kasserine', 'Kebili', 'Kef', 'Mahdia', 'Manouba', 'Medenine', 'Monastir', 'Nabeul',
    'Sfax', 'Sidi Bouzid', 'Siliana', 'Sousse', 'Tataouine', 'Tozeur', 'Tunis', 'Zaghouan'
  ];

  // Edit Modal State
  editingRow: ImportRowResult | null = null;
  editData: any = {};
  editErrors: string[] = [];

  // Preview table filter + search + pagination
  filterStatus: 'all' | 'valid' | 'error' | 'warning' | 'already_exists' = 'all';
  tableSearch = '';
  tablePage = 1;
  tablePageSize = 10;

  setFilterStatus(status: 'all' | 'valid' | 'error' | 'warning' | 'already_exists') {
    this.filterStatus = status;
    this.tablePage = 1;
    if (this.step === 'preview') this.loadStagingData();
  }

  onSearchChange() {
    this.tablePage = 1;
    if (this.step === 'preview') this.loadStagingData();
  }

  // Expose Math for template
  Math = Math;

  private companyService = inject(CompanyService);
  private router = inject(Router);

  ngOnInit() {
    this.companyService.getSectors().subscribe(res => this.sectors = res);
    this.companyService.getActivities().subscribe(res => this.activities = res);
  }

  get filteredAndSearched(): ImportRowResult[] {
    return this.pagedRowsFromServer; // No client-side filtering needed anymore
  }

  get totalTablePages(): number {
    return Math.ceil(this.totalRowsFromServer / this.tablePageSize);
  }

  get tablePages(): number[] {
    const total = this.totalTablePages;
    const current = this.tablePage;
    const pages: number[] = [];
    for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
      pages.push(i);
    }
    return pages;
  }

  get pagedRows(): ImportRowResult[] {
    return this.pagedRowsFromServer;
  }

  changePage(page: number) {
    if (page >= 1 && page <= this.totalTablePages) {
      this.tablePage = page;
      this.loadStagingData();
    }
  }

  get validRows(): any[] {
    return []; // We don't need this anymore, confirm uses sessionId
  }

  /** Count rows whose errors contain "already exists in the database" */
  get alreadyExists(): number {
    // In staging, we just show the summary from backend if possible, or 0 since we can't easily count duplicates without fetching all.
    return 0; 
  }

  /** Count rows whose errors contain "appears more than once" */
  get duplicateRows(): number {
    return 0;
  }

  isDuplicate(row: ImportRowResult): boolean {
    return row.errors.some(e => e.includes('appears more than once'));
  }

  isAlreadyExists(row: ImportRowResult): boolean {
    return row.errors.some(e => e.includes('already exists in the database'));
  }

  // ── File picking / drag-drop ──────────────────────────────────
  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }
  onDragLeave() { this.isDragOver = false; }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) this.handleFile(file);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.handleFile(file);
  }

  triggerFilePicker() { this.fileInputRef.nativeElement.click(); }

  handleFile(file: File) {
    this.uploadError = '';
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      this.uploadError = 'Only .xlsx or .xls files are supported.';
      return;
    }
    this.selectedFile = file;
    this.uploadPreview();
  }

  // ── Edit Modal Logic ──────────────────────────────────────────
  openEditModal(row: ImportRowResult) {
    this.editingRow = row;
    this.editErrors = [];
    // Deep copy data so we don't mutate original yet
    this.editData = { ...row.data };
  }

  closeEditModal() {
    this.editingRow = null;
  }

  saveEdit() {
    this.editErrors = [];
    // Basic validation
    if (!this.editData.identifier?.trim()) this.editErrors.push('Identifier is required.');
    if (!this.editData.company_name?.trim()) this.editErrors.push('Company Name is required.');
    if (!this.editData.sector_id) this.editErrors.push('Sector is required.');
    if (!this.editData.activity_id) this.editErrors.push('Activity is required.');

    if (this.editErrors.length > 0) return;

    if (this.editingRow && this.previewData) {
      this.companyService.updateStagingRow(this.sessionId, this.editingRow.row_number, this.editData).subscribe(() => {
         this.loadStagingData(); // refresh the page
         
         // Update previewData summary counts optimistically if we fixed an error
         if (this.editingRow!.status === 'error') {
            this.previewData.error_count = Math.max(0, this.previewData.error_count - 1);
            this.previewData.valid_count++;
         }
         this.closeEditModal();
      });
    }
  }

  // ── API calls ─────────────────────────────────────────────────
  uploadPreview() {
    if (!this.selectedFile) return;
    this.step = 'loading';
    this.uploadError = '';

    this.companyService.previewImport(this.selectedFile).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.startPolling();
      },
      error: (err) => {
        this.uploadError = err.error?.detail || 'Failed to start processing. Please try again.';
        this.step = 'upload';
        this.selectedFile = null;
      }
    });
  }

  startPolling() {
    this.pollingInterval = setInterval(() => {
      this.companyService.checkImportSession(this.sessionId).subscribe((data) => {
        if (data.status === 'completed') {
          clearInterval(this.pollingInterval);
          this.previewData = data;
          this.tablePage = 1;
          this.loadStagingData();
          this.step = 'preview';
        } else if (data.status === 'failed') {
          clearInterval(this.pollingInterval);
          if (data.error_message && data.error_message.startsWith('Invalid file template. Missing required columns:')) {
            const cols = data.error_message.split(':')[1].trim();
            this.uploadError = this.translate.instant('COMPANIES.IMPORT.ERR_MISSING_COLS', { cols });
          } else {
            this.uploadError = data.error_message || 'Validation failed.';
          }
          this.step = 'upload';
        }
      });
    }, 2000);
  }

  loadStagingData() {
    this.companyService.getImportStaging(this.sessionId, this.tablePage, this.tablePageSize, this.filterStatus)
      .subscribe((res) => {
        this.pagedRowsFromServer = res.rows;
        this.totalRowsFromServer = res.total_rows;
      });
  }

  goToConfirm() {
    this.step = 'confirming';
  }

  confirmImport() {
    if (!this.previewData || this.previewData.valid_count === 0) return;
    this.isConfirming = true;

    this.companyService.confirmImport(this.sessionId).subscribe({
      next: (result) => {
        this.confirmResult = result;
        this.isConfirming = false;
        this.step = 'done';
      },
      error: (err) => {
        this.isConfirming = false;
        this.uploadError = err.error?.detail || 'Import failed. Please try again.';
        this.step = 'preview';
      }
    });
  }

  reset() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    if (this.sessionId && this.step !== 'done') {
      this.companyService.cancelImportSession(this.sessionId).subscribe({
        error: (err) => console.error('Error cancelling session', err)
      });
    }
    this.sessionId = '';
    this.step = 'upload';
    this.selectedFile = null;
    this.previewData = null;
    this.confirmResult = null;
    this.uploadError = '';
    this.filterStatus = 'all';
    this.tableSearch = '';
    this.tablePage = 1;
    this.isConfirming = false;
    if (this.fileInputRef) this.fileInputRef.nativeElement.value = '';
  }

  goToCompanies() { this.router.navigate(['/admin/companies']); }

  downloadTemplate() { this.companyService.downloadTemplate(); }

  ngOnDestroy() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    if (this.sessionId && this.step !== 'done') {
      this.companyService.cancelImportSession(this.sessionId).subscribe({
        error: (err) => console.error('Error cancelling session', err)
      });
    }
  }
}
