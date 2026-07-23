import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';

function passwordRequirementsValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value || '';
  const errors: string[] = [];
  if (value.length < 8)            errors.push('minLength');
  if (!/[A-Z]/.test(value))        errors.push('uppercase');
  if (!/[a-z]/.test(value))        errors.push('lowercase');
  if (!/[0-9]/.test(value))        errors.push('digit');
  if (!/[^A-Za-z0-9]/.test(value)) errors.push('special');
  return errors.length ? { requirements: errors } : null;
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './profile.html',
  styleUrls: ['./profile.css']
})
export class ProfileComponent implements OnInit {
  public authService = inject(AuthService); // Make public for template if needed
  private fb = inject(FormBuilder);

  profileData: any = null;
  loadingProfile = true;

  profileForm: FormGroup;
  passwordForm: FormGroup;

  profileUpdating = false;
  profileSuccess = false;
  profileError = '';

  passwordUpdating = false;
  passwordSuccess = false;
  passwordError = '';

  constructor() {
    this.profileForm = this.fb.group({
      first_name: [''],
      last_name: [''],
      phone_number: [''],
      preferred_language: ['fr']
    });

    this.passwordForm = this.fb.group({
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, passwordRequirementsValidator]],
      confirm_password: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });
  }

  get passwordReqs() {
    const v = this.passwordForm.get('new_password')?.value || '';
    return {
      minLength:  v.length >= 8,
      uppercase:  /[A-Z]/.test(v),
      lowercase:  /[a-z]/.test(v),
      digit:      /[0-9]/.test(v),
      special:    /[^A-Za-z0-9]/.test(v),
    };
  }

  passwordMatchValidator(g: FormGroup) {
    return g.get('new_password')?.value === g.get('confirm_password')?.value
      ? null : { mismatch: true };
  }

  ngOnInit() {
    this.loadProfile();
  }

  loadProfile() {
    this.loadingProfile = true;
    this.authService.getMe().subscribe({
      next: (data) => {
        this.profileData = data;
        this.profileForm.patchValue({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          phone_number: data.phone_number || '',
          preferred_language: data.preferred_language || 'fr'
        });
        this.loadingProfile = false;
      },
      error: (err) => {
        console.error('Failed to load profile', err);
        this.loadingProfile = false;
      }
    });
  }

  getInitials(): string {
    if (!this.profileData) return '??';
    if (this.profileData.first_name && this.profileData.last_name) {
      return (this.profileData.first_name[0] + this.profileData.last_name[0]).toUpperCase();
    }
    return this.profileData.email ? this.profileData.email.substring(0, 2).toUpperCase() : '??';
  }

  getRoleLabel(): string {
    if (!this.profileData) return '';
    const roles: Record<string, string> = {
      'SYSTEM_ADMINISTRATOR': 'System Administrator',
      'ACCOUNT_MANAGER': 'Account Manager',
      'COMPANY_CONTACT': 'Company Contact',
      'SURVEY_RESPONDENT': 'Survey Respondent',
      'SURVEY_SUPERVISOR': 'Survey Supervisor',
      'SURVEY_AGENT': 'Survey Agent'
    };
    return roles[this.profileData.role] || this.profileData.role;
  }

  updateProfile() {
    if (this.profileForm.invalid) return;
    this.profileUpdating = true;
    this.profileSuccess = false;
    this.profileError = '';

    this.authService.updateProfile(this.profileForm.value).subscribe({
      next: () => {
        this.profileUpdating = false;
        this.profileSuccess = true;
        this.loadProfile(); // refresh data
        setTimeout(() => this.profileSuccess = false, 3000);
        
        // Also update the local storage user language if changed
        if (this.profileForm.value.preferred_language) {
          const user = this.authService.getCurrentUser();
          if (user) {
            user.preferred_language = this.profileForm.value.preferred_language;
            localStorage.setItem(this.authService.USER_KEY, JSON.stringify(user));
          }
        }
      },
      error: (err) => {
        this.profileUpdating = false;
        this.profileError = err.error?.detail || 'Failed to update profile.';
      }
    });
  }

  updatePassword() {
    if (this.passwordForm.invalid) return;
    this.passwordUpdating = true;
    this.passwordSuccess = false;
    this.passwordError = '';

    const payload = {
      current_password: this.passwordForm.value.current_password,
      new_password: this.passwordForm.value.new_password
    };

    this.authService.updateProfilePassword(payload).subscribe({
      next: () => {
        this.passwordUpdating = false;
        this.passwordSuccess = true;
        this.passwordForm.reset();
        setTimeout(() => this.passwordSuccess = false, 3000);
      },
      error: (err) => {
        this.passwordUpdating = false;
        this.passwordError = err.error?.detail || 'Failed to update password.';
      }
    });
  }
}
