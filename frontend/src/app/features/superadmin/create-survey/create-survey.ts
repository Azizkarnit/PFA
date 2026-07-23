import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SurveyService, AssignedAdmin } from '../../../core/services/survey.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-create-survey',
  imports: [RouterLink, CommonModule, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './create-survey.html',
})
export class CreateSurvey implements OnInit {
  createForm!: FormGroup;
  isSubmitting = false;
  codeAvailable: boolean | null = null;
  codeCheckPending = false;
  errorMessage = '';

  periodicities = ['ANNUAL', 'SEMI_ANNUAL', 'QUARTERLY', 'MONTHLY', 'BIENNIAL', 'CUSTOM'];
  surveyAdmins: AssignedAdmin[] = [];

  private fb = inject(FormBuilder);
  private surveyService = inject(SurveyService);
  private router = inject(Router);
  private authService = inject(AuthService);

  get canManageAdmins(): boolean {
    const user = this.authService.getCurrentUser();
    return user ? user.role === 'SYSTEM_ADMINISTRATOR' : false;
  }

  ngOnInit(): void {
    this.createForm = this.fb.group({
      code: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9_-]+$/)]],
      name: ['', Validators.required],
      description: [''],
      periodicity: ['', Validators.required],
      assigned_admin_ids: [[], this.canManageAdmins ? Validators.required : null],
      status: ['INACTIVE', Validators.required]
    });

    if (!this.canManageAdmins) {
      const user = this.authService.getCurrentUser();
      if (user && user.user_id) {
        this.createForm.patchValue({ assigned_admin_ids: [user.user_id] });
      }
    }

    this.loadLookups();
  }

  loadLookups(): void {

    this.surveyService.getSurveyAdmins().subscribe({
      next: res => this.surveyAdmins = res,
      error: err => {
        console.error('Error loading admins', err);
        this.errorMessage = 'Failed to load administrators.';
      }
    });
  }

  onCodeBlur(): void {
    const code = this.createForm.get('code')?.value?.trim();
    if (!code || this.createForm.get('code')?.invalid) {
      this.codeAvailable = null;
      return;
    }
    this.codeCheckPending = true;
    this.surveyService.checkCodeAvailable(code).subscribe({
      next: res => {
        this.codeAvailable = res.available;
        this.codeCheckPending = false;
      },
      error: () => { this.codeCheckPending = false; }
    });
  }

  isAdminSelected(adminId: number): boolean {
    const ids: number[] = this.createForm.get('assigned_admin_ids')?.value || [];
    return ids.includes(adminId);
  }

  toggleAdmin(adminId: number): void {
    const ctrl = this.createForm.get('assigned_admin_ids');
    const ids: number[] = [...(ctrl?.value || [])];
    const idx = ids.indexOf(adminId);
    if (idx > -1) ids.splice(idx, 1);
    else ids.push(adminId);
    ctrl?.setValue(ids);
  }

  onSubmit(): void {
    if (this.createForm.invalid || this.codeAvailable === false) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.isSubmitting = true;
    const v = this.createForm.value;
    this.surveyService.createSurvey({
      code: v.code.toUpperCase(),
      name: v.name,
      description: v.description || undefined,
      periodicity: v.periodicity,
      assigned_admin_ids: v.assigned_admin_ids,
      status: v.status
    }).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/admin/surveys']);
      },
      error: err => {
        this.isSubmitting = false;
        this.errorMessage = err.error?.detail || 'Error creating survey';
        console.error('Error creating survey', err);
      }
    });
  }
}
