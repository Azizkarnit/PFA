import { Component, signal, inject, computed } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { TranslateService, TranslatePipe } from '@ngx-translate/core';
import { LanguageService } from '../../../core/services/language.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);
  public translate = inject(TranslateService);

  private langService = inject(LanguageService);

  showPassword = signal(false);
  isLoading = signal(false);
  errorMessage = signal('');

  currentLang = this.langService.currentLang;
  dir = computed(() => this.currentLang() === 'ar' ? 'rtl' : 'ltr');

  constructor() {
    // Language is already set by LanguageService.init() in App root
  }

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(1)]]
  });

  setLanguage(lang: string) {
    const lowerLang = lang.toLowerCase();
    this.langService.use(lowerLang);
    this.errorMessage.set('');
  }

  togglePassword() {
    this.showPassword.update(v => !v);
  }

  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    this.auth.login({
      email: this.form.value.email!,
      password: this.form.value.password!
    }).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        if (res.require_otp) {
          sessionStorage.setItem('ins_otp_email', res.email || this.form.value.email!);
          sessionStorage.setItem('ins_otp_email_sent', res.email_sent ? 'true' : 'false');
          this.router.navigate(['/otp']);
        } else if (res.first_login) {
          this.router.navigate(['/change-password']);
        } else {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(
          err.error?.detail || this.translate.instant('LOGIN.ERR_LOGIN')
        );
      }
    });
  }

  get emailControl() { return this.form.get('email'); }
  get passwordControl() { return this.form.get('password'); }
}
