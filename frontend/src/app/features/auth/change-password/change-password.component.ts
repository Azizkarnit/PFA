import { Component, signal, inject, computed } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { AuthService } from '../../../core/services/auth.service';
import { TranslateService, TranslatePipe } from '@ngx-translate/core';
import { LanguageService } from '../../../core/services/language.service';

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

function matchPasswordsValidator(group: AbstractControl): ValidationErrors | null {
  const pw  = group.get('newPassword')?.value;
  const cpw = group.get('confirmPassword')?.value;
  return pw && cpw && pw !== cpw ? { mismatch: true } : null;
}

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './change-password.component.html',
  styleUrl: './change-password.component.css',
})
export class ChangePasswordComponent {
  private fb        = inject(FormBuilder);
  private auth      = inject(AuthService);
  private router    = inject(Router);
  private translate = inject(TranslateService);
  private langService = inject(LanguageService);

  showNew     = signal(false);
  showConfirm = signal(false);
  isLoading   = signal(false);
  errorMsg    = signal('');
  currentLang = this.langService.currentLang;

  form = this.fb.group(
    {
      newPassword:     ['', [Validators.required, passwordRequirementsValidator]],
      confirmPassword: ['', [Validators.required]],
    },
    { validators: matchPasswordsValidator }
  );

  // Convert form valueChanges to a signal so computed() can react to it
  private formValue = toSignal(this.form.valueChanges, {
    initialValue: this.form.value
  });

  req = computed(() => {
    const v = this.formValue()?.newPassword ?? '';
    return {
      minLength:  v.length >= 8,
      uppercase:  /[A-Z]/.test(v),
      lowercase:  /[a-z]/.test(v),
      digit:      /[0-9]/.test(v),
      special:    /[^A-Za-z0-9]/.test(v),
    };
  });

  strengthScore = computed(() =>
    Object.values(this.req()).filter(Boolean).length
  );

  strengthLabel = computed(() => {
    const s = this.strengthScore();
    if (s === 0) return 'CHANGE_PASSWORD.STRENGTH_NONE';
    if (s === 1) return 'CHANGE_PASSWORD.STRENGTH_VERY_WEAK';
    if (s === 2) return 'CHANGE_PASSWORD.STRENGTH_WEAK';
    if (s === 3) return 'CHANGE_PASSWORD.STRENGTH_MEDIUM';
    if (s === 4) return 'CHANGE_PASSWORD.STRENGTH_STRONG';
    return 'CHANGE_PASSWORD.STRENGTH_VERY_STRONG';
  });

  strengthColor = computed(() => {
    const s = this.strengthScore();
    if (s === 0) return '#e2e8f0';
    if (s === 1) return '#ef4444';
    if (s === 2) return '#f97316';
    if (s === 3) return '#eab308';
    if (s === 4) return '#22c55e';
    return '#16a34a';
  });

  setLanguage(lang: string) {
    this.langService.use(lang);
  }

  onSubmit() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    this.isLoading.set(true);
    this.errorMsg.set('');

    this.auth.changePassword(this.form.value.newPassword!).subscribe({
      next: () => {
        this.isLoading.set(false);
        // Update stored user to reflect first_login is now false
        const stored = this.auth.getCurrentUser();
        if (stored) {
          stored.first_login = false;
          localStorage.setItem('ins_user', JSON.stringify(stored));
        }
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        this.isLoading.set(false);
        this.errorMsg.set(err.error?.detail || 'Une erreur est survenue. Veuillez réessayer.');
      }
    });
  }
}
