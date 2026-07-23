import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SurveyService, Survey, AssignedAdmin } from '../../../core/services/survey.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-surveys',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './surveys.html',

  styles: `
    .status-badge {
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 20px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .btn-icon {
      width: 32px; height: 32px;
      display: flex; align-items: center; justify-content: center;
      padding: 0; border: none;
    }
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 2000;
      display: flex; align-items: center; justify-content: center;
    }
    .form-section-title {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #6c757d;
      margin-bottom: 12px;
    }
    .badge-pill-custom {
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 0.72rem;
      font-weight: 600;
    }
  `
})
export class Surveys implements OnInit {
  private surveyService = inject(SurveyService);
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);

  get canManageAdmins(): boolean {
    const user = this.authService.getCurrentUser();
    return user ? user.role === 'SYSTEM_ADMINISTRATOR' : false;
  }

  // ── Data ────────────────────────────────────────────────────────────────────
  surveys: Survey[] = [];
  periodicities = ['ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'MONTHLY', 'BIENNIAL', 'CUSTOM'];
  surveyAdmins: AssignedAdmin[] = [];
  filterAdmins: AssignedAdmin[] = [];

  // ── Pagination ──────────────────────────────────────────────────────────────
  currentPage = 1;
  pageSize = 10;
  totalItems = 0;

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalItems / this.pageSize));
  }

  get startIndex(): number {
    return this.totalItems === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalItems);
  }

  // ── Filters ─────────────────────────────────────────────────────────────────
  searchInput = '';
  searchQuery = '';
  selectedStatus = 'ALL';
  selectedPeriodicity = '';
  selectedAdminId = 0;

  // ── Loading ─────────────────────────────────────────────────────────────────
  isLoading = false;

  // ── Create Modal ─────────────────────────────────────────────────────────────
  isSubmitting = false;

  // ── Edit Modal ──────────────────────────────────────────────────────────────
  showEditModal = false;
  editingSurvey: Survey | null = null;
  editForm!: FormGroup;
  isEditSubmitting = false;

  // ── Confirm Modal ────────────────────────────────────────────────────────────
  confirmModal: {
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel: string;
    confirmClass: string;
    onConfirm?: () => void;
  } = { isOpen: false, title: '', message: '', confirmLabel: 'Confirm', confirmClass: 'btn-danger' };

  // ─────────────────────────────────────────────────────────────────────────────
  ngOnInit(): void {

    this.editForm = this.fb.group({
      name: ['', Validators.required],
      description: [''],
      periodicity: ['', Validators.required],
      assigned_admin_ids: [[], Validators.required],
      status: ['', Validators.required]
    });

    this.loadLookups();
    this.loadData();
  }

  // ─── Loaders ─────────────────────────────────────────────────────────────────

  loadLookups(): void {
    this.surveyService.getSurveyAdmins().subscribe({
      next: res => this.surveyAdmins = res,
      error: err => console.error('Error loading admins', err)
    });
    
    this.surveyService.getAssignedAdminsFilter().subscribe({
      next: res => this.filterAdmins = res,
      error: err => console.error('Error loading filter admins', err)
    });
  }

  loadData(): void {
    this.isLoading = true;
    const skip = (this.currentPage - 1) * this.pageSize;
    this.surveyService.getSurveys(
      skip, this.pageSize,
      this.searchQuery || undefined,
      this.selectedStatus !== 'ALL' ? this.selectedStatus : undefined,
      this.selectedPeriodicity || undefined,
      this.selectedAdminId || undefined
    ).subscribe({
      next: res => {
        this.surveys = res.items;
        this.totalItems = res.total_count;
        this.isLoading = false;
      },
      error: err => {
        console.error('Error loading surveys', err);
        this.isLoading = false;
      }
    });
  }

  // ─── Search & Filters ─────────────────────────────────────────────────────────

  onSearch(): void {
    this.searchQuery = this.searchInput;
    this.currentPage = 1;
    this.loadData();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadData();
  }

  clearFilters(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.searchInput = '';
    this.searchQuery = '';
    this.selectedStatus = 'ALL';
    this.selectedPeriodicity = '';
    this.selectedAdminId = 0;
    this.currentPage = 1;
    this.loadData();
  }

  // ─── Pagination ───────────────────────────────────────────────────────────────

  nextPage(): void {
    if (this.currentPage * this.pageSize < this.totalItems) {
      this.currentPage++;
      this.loadData();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadData();
    }
  }


  // ─── Edit Survey ──────────────────────────────────────────────────────────────

  isEditAdminSelected(adminId: number): boolean {
    const ids: number[] = this.editForm.get('assigned_admin_ids')?.value || [];
    return ids.includes(adminId);
  }

  toggleEditAdmin(adminId: number): void {
    const ctrl = this.editForm.get('assigned_admin_ids');
    const ids: number[] = [...(ctrl?.value || [])];
    const idx = ids.indexOf(adminId);
    if (idx > -1) ids.splice(idx, 1);
    else ids.push(adminId);
    ctrl?.setValue(ids);
  }


  openEditModal(survey: Survey, event: Event): void {
    event.stopPropagation();
    this.editingSurvey = survey;
    this.editForm.patchValue({
      name: survey.name,
      description: survey.description || '',
      periodicity: survey.periodicity,
      assigned_admin_ids: survey.assigned_admins.map(a => a.id),
      status: survey.status
    });
    this.showEditModal = true;
  }

  closeEditModal(): void {
    this.showEditModal = false;
    this.editingSurvey = null;
  }

  submitEdit(): void {
    if (this.editForm.invalid || !this.editingSurvey) return;
    this.isEditSubmitting = true;
    const v = this.editForm.value;
    this.surveyService.updateSurvey(this.editingSurvey.id, {
      name: v.name,
      description: v.description || undefined,
      periodicity: v.periodicity,
      assigned_admin_ids: v.assigned_admin_ids,
      status: v.status
    }).subscribe({
      next: () => {
        this.isEditSubmitting = false;
        this.closeEditModal();
        this.loadData();
      },
      error: err => {
        this.isEditSubmitting = false;
        console.error('Error updating survey', err);
      }
    });
  }

  // ─── Archive ──────────────────────────────────────────────────────────────────

  confirmArchive(survey: Survey, event: Event): void {
    event.stopPropagation();
    this.confirmModal = {
      isOpen: true,
      title: 'Archive Survey',
      message: `Are you sure you want to archive "${survey.name}"? Archived surveys remain readable but can no longer be activated.`,
      confirmLabel: 'Archive',
      confirmClass: 'btn-warning',
      onConfirm: () => {
        this.surveyService.updateSurveyStatus(survey.id, 'ARCHIVED').subscribe({
          next: () => this.loadData(),
          error: err => console.error('Error archiving survey', err)
        });
      }
    };
  }

  closeConfirmModal(): void {
    this.confirmModal.isOpen = false;
  }

  doConfirm(): void {
    if (this.confirmModal.onConfirm) this.confirmModal.onConfirm();
    this.closeConfirmModal();
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────────

  getStatusClass(status: string): string {
    switch (status) {
      case 'ACTIVE': return 'bg-success bg-opacity-10 text-success border border-success border-opacity-25';
      case 'INACTIVE': return 'bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25';
      case 'ARCHIVED': return 'bg-warning bg-opacity-10 text-warning border border-warning border-opacity-25';
      default: return 'bg-light text-muted';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'ACTIVE': return 'Active';
      case 'INACTIVE': return 'Inactive';
      case 'ARCHIVED': return 'Archived';
      default: return status;
    }
  }

  getLastPassageLabel(survey: Survey): string {
    if (!survey.last_passage_year) return '—';
    return `${survey.last_passage_year} / P${survey.last_passage_number}`;
  }

  get hasActiveFilters(): boolean {
    return !!(this.searchQuery || this.selectedStatus !== 'ALL' || this.selectedPeriodicity || this.selectedAdminId);
  }
}
