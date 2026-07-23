import { LanguageService } from '../../../core/services/language.service';
import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function futureDateValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (!control.value) return null;
    const inputDate = new Date(control.value);
    const now = new Date();
    if (inputDate <= now) {
      return { futureDate: true };
    }
    return null;
  };
}
import {
  SurveyService, Survey, Passage, AssignedAdmin,
  Questionnaire, SampleInfo, SurveyMonitoring, ResultFile
} from '../../../core/services/survey.service';
import { CompanyService } from '../../../core/services/company.service';
import { Sector } from '../../../core/services/company.service';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';

type Tab = 'overview' | 'passages' | 'questionnaire' | 'samples' | 'monitoring' | 'reports' | 'results';

@Component({
  selector: 'app-survey-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './survey-detail.html',
  styles: `
    .tab-nav { display:flex; gap:2px; border-bottom:2px solid #e9ecef; overflow-x:auto; scrollbar-width:none; }
    .tab-nav::-webkit-scrollbar { display:none; }
    .tab-btn { padding:10px 18px; border:none; background:transparent; color:#6c757d; font-weight:600; font-size:.85rem; border-bottom:2px solid transparent; margin-bottom:-2px; white-space:nowrap; cursor:pointer; transition:color .15s,border-color .15s; display:flex; align-items:center; gap:6px; }
    .tab-btn:hover { color:#0d6efd; }
    .tab-btn.active { color:#0d6efd; border-bottom-color:#0d6efd; }
    .info-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:16px; }
    .info-label { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#6c757d; }
    .info-value { font-weight:600; color:#212529; font-size:.9rem; margin-top:3px; }
    .stat-card { background:white; border:1px solid #e9ecef; border-radius:10px; padding:20px; }
    .stat-number { font-size:2rem; font-weight:800; line-height:1; }
    .badge-status { font-size:.72rem; padding:4px 12px; border-radius:20px; font-weight:700; }
    .pstatus-badge { font-size:.7rem; padding:3px 10px; border-radius:20px; font-weight:700; }
    .modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:2000; display:flex; align-items:center; justify-content:center; padding:16px; }
    .passage-row:hover { background:#f8f9fa; }
    .progress-bar-track { height:8px; background:#e9ecef; border-radius:4px; overflow:hidden; }
    .progress-bar-fill { height:100%; border-radius:4px; transition:width .4s ease; }
    .upload-zone { border:2px dashed #dee2e6; border-radius:10px; padding:40px; text-align:center; cursor:pointer; transition:border-color .2s,background .2s; }
    .upload-zone:hover, .upload-zone.drag-over { border-color:#0d6efd; background:#f0f4ff; }
    .file-icon-pdf { color:#dc3545; }
    .file-icon-excel { color:#198754; }
  `
})
export class SurveyDetail implements OnInit {
  public langService = inject(LanguageService);

  

  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private surveyService = inject(SurveyService);
  private companyService = inject(CompanyService);
  private fb = inject(FormBuilder);
  private cdr = inject(ChangeDetectorRef);
  private authService = inject(AuthService);

  get canManageAdmins(): boolean {
    const user = this.authService.getCurrentUser();
    return user ? user.role === 'SYSTEM_ADMINISTRATOR' : false;
  }

  // ── State ──────────────────────────────────────────────────────────────────
  surveyId!: number;
  survey: Survey | null = null;
  isLoading = true;
  activeTab: Tab = 'overview';

  tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'overview',      label: 'Overview',      icon: 'info' },
    { id: 'passages',      label: 'Passages',       icon: 'calendar_month' },
    { id: 'questionnaire', label: 'Questionnaire',  icon: 'quiz' },
    { id: 'samples',       label: 'Samples',        icon: 'group' },
    { id: 'monitoring',    label: 'Monitoring',     icon: 'monitoring' },
    { id: 'reports',       label: 'Reports',        icon: 'assessment' },
    { id: 'results',       label: 'Results',        icon: 'upload_file' },
  ];

  // ── Lookups ────────────────────────────────────────────────────────────────
  periodicities = ['ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'MONTHLY', 'BIENNIAL', 'CUSTOM'];
  surveyAdmins: AssignedAdmin[] = [];
  sectors: Sector[] = [];

  // ── Passages ───────────────────────────────────────────────────────────────
  passages: Passage[] = [];
  passagesLoading = false;
  showPassageModal = false;
  passageForm!: FormGroup;
  isPassageSubmitting = false;
  editingPassage: Passage | null = null;
  selectedPassage: Passage | null = null;  // passage selected for questionnaire/sample tabs

  // ── Questionnaire ──────────────────────────────────────────────────────────
  questionnaire: Questionnaire | null = null;
  questionnaireLoading = false;
  questionnaireForm!: FormGroup;
  isQSaving = false;
  selectedPdfFile: File | null = null;
  isPdfUploading = false;

  // ── Sample ─────────────────────────────────────────────────────────────────
  sample: SampleInfo | null = null;
  sampleLoading = false;
  isSampleUploading = false;
  selectedSampleFile: File | null = null;

  // ── Monitoring ─────────────────────────────────────────────────────────────
  monitoring: SurveyMonitoring | null = null;
  monitoringLoading = false;

  // ── Results ────────────────────────────────────────────────────────────────
  resultFiles: ResultFile[] = [];
  resultsLoading = false;
  selectedResultFile: File | null = null;
  selectedSectorId: number | null = null;
  isResultUploading = false;

  // ── Edit Survey Modal ──────────────────────────────────────────────────────
  showEditModal = false;
  editForm!: FormGroup;
  isEditSubmitting = false;

  // ── Confirm Modal ──────────────────────────────────────────────────────────
  confirmModal: { isOpen: boolean; title: string; message: string; confirmLabel: string; confirmClass: string; onConfirm?: () => void; } =
    { isOpen: false, title: '', message: '', confirmLabel: 'Confirm', confirmClass: 'btn-danger' };

  // ── Alert Modal ────────────────────────────────────────────────────────────
  alertModal: { isOpen: boolean; title: string; message: string; type: 'error' | 'info' | 'success' } = { isOpen: false, title: '', message: '', type: 'error' };

  openAlertModal(title: string, message: string, type: 'error' | 'info' | 'success' = 'error'): void {
    this.alertModal = { isOpen: true, title, message, type };
  }
  closeAlertModal(): void {
    this.alertModal.isOpen = false;
  }

  // ─────────────────────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.surveyId = Number(this.route.snapshot.paramMap.get('id'));
    this.editForm = this.fb.group({
      name: ['', Validators.required], description: [''],
      periodicity: ['', Validators.required], assigned_admin_ids: [[]], status: ['', Validators.required]
    });
    this.passageForm = this.fb.group({
      year: [new Date().getFullYear(), [Validators.required, Validators.min(2000), Validators.max(2100)]],
      passage_number: [1, [Validators.required, Validators.min(1)]],
      opening_date: ['', Validators.required],
      closing_date: ['', [Validators.required, futureDateValidator()]],
    });
    this.questionnaireForm = this.fb.group({
      questionnaire_url: [''],
      version: ['1.0', Validators.required],
    });
    this.loadSurvey();
    this.loadLookups();
  }

  // ── Loaders ────────────────────────────────────────────────────────────────
  loadSurvey(): void {
    this.isLoading = true;
    this.surveyService.getSurvey(this.surveyId).subscribe({
      next: s => { this.survey = s; this.isLoading = false; },
      error: () => { this.isLoading = false; this.router.navigate(['/admin/surveys']); }
    });
  }

  refreshCurrentView(): void {
    this.loadSurvey();
    if (this.activeTab === 'passages') this.loadPassages();
    else if (this.activeTab === 'questionnaire') this.loadQuestionnaire();
    else if (this.activeTab === 'samples') this.loadSample();
    else if (this.activeTab === 'monitoring') this.loadMonitoring();
    else if (this.activeTab === 'results') this.loadResults();
  }

  loadLookups(): void {
    this.surveyService.getSurveyAdmins().subscribe({ next: r => this.surveyAdmins = r });
    this.companyService.getSectors().subscribe({ next: r => this.sectors = r });
  }

  loadPassages(): void {
    this.passagesLoading = true;
    this.surveyService.getPassages(this.surveyId).subscribe({
      next: r => { 
        this.passages = r.items; 
        this.passagesLoading = false;
        if (!this.selectedPassage && r.items.length > 0) { 
          this.selectedPassage = r.items[0]; 
          // Load tab-specific data once a passage is selected
          if (this.activeTab === 'questionnaire') this.loadQuestionnaire();
          if (this.activeTab === 'samples') this.loadSample();
        }
      },
      error: () => { this.passagesLoading = false; }
    });
  }

  loadQuestionnaire(): void {
    if (!this.selectedPassage) return;
    this.questionnaireLoading = true;
    this.surveyService.getQuestionnaire(this.surveyId, this.selectedPassage.id).subscribe({
      next: q => { this.questionnaire = q; this.questionnaireLoading = false;
        if (q) { this.questionnaireForm.patchValue({ questionnaire_url: q.questionnaire_url || '', version: q.version }); }
      },
      error: () => { this.questionnaireLoading = false; }
    });
  }

  loadSample(): void {
    if (!this.selectedPassage) return;
    this.sampleLoading = true;
    this.surveyService.getSample(this.surveyId, this.selectedPassage.id).subscribe({
      next: s => { this.sample = s; this.sampleLoading = false; },
      error: () => { this.sampleLoading = false; }
    });
  }

  loadMonitoring(): void {
    this.monitoringLoading = true;
    this.surveyService.getMonitoring(this.surveyId).subscribe({
      next: m => { this.monitoring = m; this.monitoringLoading = false; },
      error: () => { this.monitoringLoading = false; }
    });
  }

  loadResults(): void {
    this.resultsLoading = true;
    this.surveyService.getResults(this.surveyId).subscribe({
      next: r => { this.resultFiles = r; this.resultsLoading = false; },
      error: () => { this.resultsLoading = false; }
    });
  }

  // ── Tab switching ──────────────────────────────────────────────────────────
  setTab(tab: Tab): void {
    this.activeTab = tab;
    if (tab === 'passages' && this.passages.length === 0) this.loadPassages();
    if (tab === 'questionnaire') { 
      if (this.passages.length === 0) this.loadPassages(); 
      else this.loadQuestionnaire(); 
    }
    if (tab === 'samples') { 
      if (this.passages.length === 0) this.loadPassages(); 
      else this.loadSample(); 
    }
    if (tab === 'monitoring') this.loadMonitoring();
    if (tab === 'results') this.loadResults();
  }

  selectPassageForTab(p: Passage): void {
    this.selectedPassage = p;
    if (this.activeTab === 'questionnaire') this.loadQuestionnaire();
    if (this.activeTab === 'samples') this.loadSample();
  }

  // ── Passage Modal ──────────────────────────────────────────────────────────
  openCreatePassage(): void {
    this.editingPassage = null;
    this.passageForm.reset({ year: new Date().getFullYear(), passage_number: (this.passages.length + 1) });
    this.onPassageInputChanged(); // Trigger auto-calculation
    this.showPassageModal = true;
  }

  openEditPassage(p: Passage, e: Event): void {
    e.stopPropagation();
    this.editingPassage = p;
    const toLocal = (d: string) => d ? d.substring(0, 16) : '';
    this.passageForm.patchValue({
      year: p.year, passage_number: p.passage_number,
      opening_date: toLocal(p.opening_date), closing_date: toLocal(p.closing_date),
    });
    this.showPassageModal = true;
  }

  closePassageModal(): void { this.showPassageModal = false; this.editingPassage = null; }

  submitPassage(): void {
    if (this.passageForm.invalid) return;
    this.isPassageSubmitting = true;
    const v = this.passageForm.value;
    const payload = { year: +v.year, passage_number: +v.passage_number, opening_date: v.opening_date, closing_date: v.closing_date };

    const obs = this.editingPassage
      ? this.surveyService.updatePassage(this.surveyId, this.editingPassage.id, { opening_date: payload.opening_date, closing_date: payload.closing_date })
      : this.surveyService.createPassage(this.surveyId, payload);

    obs.subscribe({
      next: () => { this.isPassageSubmitting = false; this.closePassageModal(); this.loadPassages(); this.loadSurvey(); },
      error: err => { 
        this.isPassageSubmitting = false; 
        console.error(err); 
        this.openAlertModal('Failed to save passage', err.error?.detail || 'An error occurred.', 'error');
      }
    });
  }

  changePassageStatus(p: Passage, newStatus: string, e: Event): void {
    e.stopPropagation();
    const labels: Record<string, string> = { READY: 'Mark as Ready', OPEN: 'Activate', CLOSED: 'Close', ARCHIVED: 'Archive' };
    this.confirmModal = {
      isOpen: true,
      title: `${labels[newStatus] || newStatus} Passage`,
      message: `Change passage ${p.year}/P${p.passage_number} status to ${newStatus}?`,
      confirmLabel: labels[newStatus] || 'Confirm',
      confirmClass: newStatus === 'ARCHIVED' ? 'btn-warning' : newStatus === 'CLOSED' ? 'btn-dark' : 'btn-primary',
      onConfirm: () => {
        this.surveyService.updatePassage(this.surveyId, p.id, { status: newStatus }).subscribe({
          next: () => this.loadPassages(),
          error: err => {
            console.error(err);
            this.openAlertModal('Update Failed', err.error?.detail || 'Failed to update passage status.', 'error');
          }
        });
      }
    };
  }

  // ── Polling Helper ──────────────────────────────────────────────────────────
  pollTask(taskId: string, onSuccess: (result: any) => void, onError: (err: string) => void) {
    this.surveyService.getTaskStatus(taskId).subscribe({
      next: res => {
        if (res.status === 'SUCCESS') {
          onSuccess(res.result);
        } else if (res.status === 'FAILURE') {
          onError(res.error || 'Task failed.');
        } else {
          setTimeout(() => this.pollTask(taskId, onSuccess, onError), 1000);
        }
      },
      error: err => onError('Failed to check task status.')
    });
  }

  // ── Questionnaire ──────────────────────────────────────────────────────────
  saveQuestionnaire(): void {
    if (!this.selectedPassage) return;
    this.isQSaving = true;
    const v = this.questionnaireForm.value;
    this.surveyService.upsertQuestionnaire(this.surveyId, this.selectedPassage.id, { questionnaire_url: v.questionnaire_url || undefined, version: v.version }).subscribe({
      next: q => { this.questionnaire = q; this.isQSaving = false; },
      error: err => { 
        this.isQSaving = false; 
        console.error(err);
        this.openAlertModal('Failed to save', err.error?.detail || 'An error occurred.', 'error');
      }
    });
  }

  isPdfDragOver = false;
  onPdfDragOver(e: DragEvent): void { e.preventDefault(); this.isPdfDragOver = true; }
  onPdfDragLeave(e: DragEvent): void { e.preventDefault(); this.isPdfDragOver = false; }
  onPdfDrop(e: DragEvent): void {
    e.preventDefault();
    this.isPdfDragOver = false;
    if (e.dataTransfer?.files?.length) {
      this.selectedPdfFile = e.dataTransfer.files[0];
    }
  }

  onPdfFileSelect(e: Event): void {
    const input = e.target as HTMLInputElement;
    if (input.files?.length) this.selectedPdfFile = input.files[0];
  }

  uploadPdf(): void {
    if (!this.selectedPassage || !this.selectedPdfFile) return;
    this.isPdfUploading = true;
    this.surveyService.uploadQuestionnairePdf(this.surveyId, this.selectedPassage.id, this.selectedPdfFile).subscribe({
      next: res => {
        this.pollTask(res.task_id, (result) => {
          this.questionnaire = result;
          this.selectedPdfFile = null;
          this.isPdfUploading = false;
          this.cdr.detectChanges();
        }, (err) => {
          console.error(err);
          this.isPdfUploading = false;
          this.openAlertModal('Upload Failed', err, 'error');
          this.cdr.detectChanges();
        });
      },
      error: () => { 
        this.isPdfUploading = false; 
        this.cdr.detectChanges();
      }
    });
  }

  // ── Sample ─────────────────────────────────────────────────────────────────
  isSampleDragOver = false;
  onSampleDragOver(e: DragEvent): void { e.preventDefault(); this.isSampleDragOver = true; }
  onSampleDragLeave(e: DragEvent): void { e.preventDefault(); this.isSampleDragOver = false; }
  onSampleDrop(e: DragEvent): void {
    e.preventDefault();
    this.isSampleDragOver = false;
    if (e.dataTransfer?.files?.length) {
      this.selectedSampleFile = e.dataTransfer.files[0];
    }
  }

  onSampleFileSelect(e: Event): void {
    const input = e.target as HTMLInputElement;
    if (input.files?.length) this.selectedSampleFile = input.files[0];
  }

  uploadSample(): void {
    if (!this.selectedPassage || !this.selectedSampleFile) return;
    this.isSampleUploading = true;
    this.surveyService.uploadSample(this.surveyId, this.selectedPassage.id, this.selectedSampleFile).subscribe({
      next: res => {
        this.pollTask(res.task_id, (result) => {
          this.selectedSampleFile = null;
          this.isSampleUploading = false;
          this.loadSample(); // Fetch the full sample with companies
          this.loadPassages(); // refresh company count
          this.cdr.detectChanges();
        }, (err) => {
          console.error(err);
          this.isSampleUploading = false;
          this.openAlertModal('Sample Upload Failed', err, 'error');
          this.cdr.detectChanges();
        });
      },
      error: () => { 
        this.isSampleUploading = false; 
        this.cdr.detectChanges();
      }
    });
  }

  confirmReplaceSample(): void {
    this.confirmModal = {
      isOpen: true, title: 'Replace Sample',
      message: 'Uploading a new sample will replace the existing one. All current data will be lost.',
      confirmLabel: 'Replace', confirmClass: 'btn-danger',
      onConfirm: () => this.uploadSample()
    };
  }

  downloadTemplate(): void {
    this.surveyService.downloadSampleTemplate();
  }

  // ── Result Files ───────────────────────────────────────────────────────────
  isResultDragOver = false;
  onResultDragOver(e: DragEvent): void { e.preventDefault(); this.isResultDragOver = true; }
  onResultDragLeave(e: DragEvent): void { e.preventDefault(); this.isResultDragOver = false; }
  onResultDrop(e: DragEvent): void {
    e.preventDefault();
    this.isResultDragOver = false;
    if (e.dataTransfer?.files?.length) {
      this.selectedResultFile = e.dataTransfer.files[0];
    }
  }

  onResultFileSelect(e: Event): void {
    const input = e.target as HTMLInputElement;
    if (input.files?.length) this.selectedResultFile = input.files[0];
  }

  uploadProgress = 0;

  uploadResult(): void {
    if (!this.selectedResultFile || !this.selectedSectorId) return;
    this.isResultUploading = true;
    this.uploadProgress = 0;
    
    this.surveyService.uploadResultWithProgress(this.surveyId, this.selectedSectorId, this.selectedResultFile).subscribe({
      next: (event: HttpEvent<any>) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.uploadProgress = Math.round(100 * event.loaded / event.total);
          this.cdr.detectChanges();
        } else if (event.type === HttpEventType.Response) {
          const res = event.body;
          this.pollTask(res.task_id, (result) => {
          this.resultFiles.unshift(result);
          this.selectedResultFile = null;
          this.selectedSectorId = null;
          this.isResultUploading = false;
          this.cdr.detectChanges();
        }, (err) => {
          console.error(err);
          this.isResultUploading = false;
          this.openAlertModal('Upload Failed', err, 'error');
          this.cdr.detectChanges();
        });
        }
      },
      error: (err: any) => { 
        this.isResultUploading = false; 
        this.openAlertModal('Upload Failed', err?.error?.detail || 'An error occurred during upload.', 'error');
        this.cdr.detectChanges();
      }
    });
  }

  confirmDeleteResult(rf: ResultFile): void {
    this.confirmModal = {
      isOpen: true, title: 'Delete Result File',
      message: `Delete "${rf.file_name}"? This cannot be undone.`,
      confirmLabel: 'Delete', confirmClass: 'btn-danger',
      onConfirm: () => {
        this.surveyService.deleteResult(this.surveyId, rf.id).subscribe({ next: () => this.loadResults() });
      }
    };
  }

  downloadResult(rf: ResultFile): void {
    if (rf.file_path) {
      const filename = rf.file_path.split(/[/\\]/).pop();
      window.open(`${environment.apiUrl}/surveys/downloads/result/${filename}`, '_blank');
    }
  }

  // ── Reports Export ─────────────────────────────────────────────────────────
  isExportingExcel = false;
  isExportingPdf = false;

  exportReport(format: 'excel' | 'pdf'): void {
    if (!this.survey) return;
    if (format === 'excel') this.isExportingExcel = true;
    else this.isExportingPdf = true;

    this.surveyService.generateReport(this.surveyId, format).subscribe({
      next: res => {
        this.pollTask(res.task_id, (result) => {
          window.location.href = result.file_url;
          if (format === 'excel') this.isExportingExcel = false;
          else this.isExportingPdf = false;
        }, (err) => {
          console.error(err);
          if (format === 'excel') this.isExportingExcel = false;
          else this.isExportingPdf = false;
        });
      },
      error: () => {
        if (format === 'excel') this.isExportingExcel = false;
        else this.isExportingPdf = false;
      }
    });
  }

  // ── Edit Survey ────────────────────────────────────────────────────────────
  openEditModal(): void {
    if (!this.survey) return;
    this.editForm.patchValue({ name: this.survey.name, description: this.survey.description || '', periodicity: this.survey.periodicity, assigned_admin_ids: this.survey.assigned_admins.map(a => a.id), status: this.survey.status });
    this.showEditModal = true;
  }
  closeEditModal(): void { this.showEditModal = false; }

  isEditAdminSelected(id: number): boolean { return (this.editForm.get('assigned_admin_ids')?.value || []).includes(id); }
  toggleEditAdmin(id: number): void {
    const ctrl = this.editForm.get('assigned_admin_ids');
    const ids = [...(ctrl?.value || [])];
    const i = ids.indexOf(id); if (i > -1) ids.splice(i, 1); else ids.push(id);
    ctrl?.setValue(ids);
  }

  submitEdit(): void {
    if (this.editForm.invalid || !this.survey) return;
    this.isEditSubmitting = true;
    const v = this.editForm.value;
    this.surveyService.updateSurvey(this.survey.id, { name: v.name, description: v.description || undefined, periodicity: v.periodicity, assigned_admin_ids: v.assigned_admin_ids, status: v.status }).subscribe({
      next: s => { this.survey = s; this.isEditSubmitting = false; this.closeEditModal(); },
      error: err => { 
        this.isEditSubmitting = false; 
        console.error(err);
        this.openAlertModal('Update Failed', err.error?.detail || 'An error occurred.', 'error');
      }
    });
  }

  // ── Confirm Modal ──────────────────────────────────────────────────────────
  confirmArchiveSurvey(): void {
    if (!this.survey) return;
    this.confirmModal = {
      isOpen: true, title: 'Archive Survey',
      message: `Archive "${this.survey.name}"? The survey becomes read-only.`,
      confirmLabel: 'Archive', confirmClass: 'btn-warning',
      onConfirm: () => { this.surveyService.updateSurveyStatus(this.survey!.id, 'ARCHIVED').subscribe({ next: s => this.survey = s }); }
    };
  }
  closeConfirmModal(): void { this.confirmModal.isOpen = false; }
  doConfirm(): void { if (this.confirmModal.onConfirm) this.confirmModal.onConfirm(); this.closeConfirmModal(); }

  // ── Helpers ────────────────────────────────────────────────────────────────
  getStatusClass(s: string): string {
    return { ACTIVE: 'bg-success bg-opacity-10 text-success border border-success border-opacity-25', INACTIVE: 'bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25', ARCHIVED: 'bg-warning bg-opacity-10 text-warning border border-warning border-opacity-25' }[s] || 'bg-light text-muted';
  }
  getPassageStatusClass(s: string): string {
    return { OPEN: 'bg-success bg-opacity-10 text-success border border-success border-opacity-25', READY: 'bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25', DRAFT: 'bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25', CLOSED: 'bg-dark bg-opacity-10 text-dark border border-dark border-opacity-25', ARCHIVED: 'bg-warning bg-opacity-10 text-warning border border-warning border-opacity-25' }[s] || 'bg-light text-muted';
  }

  passageNextStatus(s: string): string | null {
    return { DRAFT: 'READY', READY: 'OPEN', OPEN: 'CLOSED' }[s] ?? null;
  }
  passageNextLabel(s: string): string {
    return { DRAFT: 'Mark Ready', READY: 'Activate', OPEN: 'Close Passage' }[s] ?? '';
  }
  passageNextClass(s: string): string {
    return { DRAFT: 'btn-outline-primary', READY: 'btn-success', OPEN: 'btn-outline-dark' }[s] ?? 'btn-outline-secondary';
  }

  get totalMonitoringCompanies(): number { return this.monitoring?.total_companies_all_passages ?? 0; }
  get totalCompleted(): number { return this.monitoring?.passages.reduce((acc, p) => acc + p.completed, 0) ?? 0; }
  get overallPct(): number { return this.totalMonitoringCompanies > 0 ? Math.round(this.totalCompleted / this.totalMonitoringCompanies * 100) : 0; }

  // ── Auto-Calculation ───────────────────────────────────────────────────────
  get currentPeriodicityCode(): string {
    return this.survey?.periodicity || '';
  }

  get isCustomPeriodicity(): boolean {
    return this.currentPeriodicityCode === 'CUSTOM';
  }

  onPassageInputChanged(): void {
    const code = this.currentPeriodicityCode;
    if (code === 'CUSTOM') return; // Do nothing for custom dates

    const year = Number(this.passageForm.get('year')?.value);
    let pNum = Number(this.passageForm.get('passage_number')?.value);

    if (!year || !pNum) return;

    // Enforce limits
    if (code === 'MONTHLY' && pNum > 12) pNum = 12;
    if (code === 'QUARTERLY' && pNum > 4) pNum = 4;
    if (code === 'SEMI_ANNUAL' && pNum > 2) pNum = 2;
    if ((code === 'ANNUAL' || code === 'BIENNIAL') && pNum > 1) pNum = 1;
    
    if (this.passageForm.get('passage_number')?.value !== pNum) {
      this.passageForm.patchValue({ passage_number: pNum }, { emitEvent: false });
    }

    // Auto-calculate dates
    let startMonth = 1;
    let endMonth = 1;
    let endYear = year;

    if (code === 'MONTHLY') {
      startMonth = pNum;
      endMonth = pNum;
    } else if (code === 'QUARTERLY') {
      startMonth = (pNum - 1) * 3 + 1;
      endMonth = startMonth + 2;
    } else if (code === 'SEMI_ANNUAL') {
      startMonth = (pNum - 1) * 6 + 1;
      endMonth = startMonth + 5;
    } else if (code === 'ANNUAL') {
      startMonth = 1;
      endMonth = 12;
    } else if (code === 'BIENNIAL') {
      startMonth = 1;
      endMonth = 12;
      endYear = year + 1;
    }

    const pad = (n: number) => n.toString().padStart(2, '0');
    
    // First day of startMonth
    const startDate = `${year}-${pad(startMonth)}-01T00:00`;
    
    // Last day of endMonth
    const lastDay = new Date(endYear, endMonth, 0).getDate();
    const endDate = `${endYear}-${pad(endMonth)}-${pad(lastDay)}T23:59`;

    this.passageForm.patchValue({
      opening_date: startDate,
      closing_date: endDate
    }, { emitEvent: false });
  }
}

