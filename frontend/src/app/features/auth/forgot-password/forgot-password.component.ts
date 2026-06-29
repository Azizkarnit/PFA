import { Component, signal, inject, computed } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { TranslateService, TranslatePipe } from '@ngx-translate/core';
import { LanguageService } from '../../../core/services/language.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, RouterLink],
  templateUrl: './forgot-password.component.html',
  styleUrl: './forgot-password.component.css'
})
export class ForgotPasswordComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);
  public translate = inject(TranslateService);
  private langService = inject(LanguageService);

  /** Controls which "page" is shown: 'request' or 'confirmation' */
  step = signal<'request' | 'confirmation'>('request');

  isLoading = signal(false);
  errorMessage = signal('');
  submittedEmail = signal('');

  currentLang = this.langService.currentLang;
  dir = computed(() => this.currentLang() === 'ar' ? 'rtl' : 'ltr');

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]]
  });

  setLanguage(lang: string) {
    this.langService.use(lang.toLowerCase());
    this.errorMessage.set('');
  }

  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    const email = this.form.value.email!;

    this.auth.forgotPassword(email).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.submittedEmail.set(email);
        this.step.set('confirmation');
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(
          err.error?.detail || this.translate.instant('FORGOT_PASSWORD.ERR_GENERIC')
        );
      }
    });
  }

  resendLink() {
    this.isLoading.set(true);
    this.auth.forgotPassword(this.submittedEmail()).subscribe({
      next: () => { this.isLoading.set(false); },
      error: () => { this.isLoading.set(false); }
    });
  }

  goBackToRequest() {
    this.step.set('request');
    this.errorMessage.set('');
  }

  get emailControl() { return this.form.get('email'); }
}
