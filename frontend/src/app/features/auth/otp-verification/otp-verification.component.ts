import { Component, signal, inject, computed, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { TranslateService, TranslatePipe } from '@ngx-translate/core';
import { LanguageService } from '../../../core/services/language.service';

@Component({
  selector: 'app-otp-verification',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, RouterLink],
  templateUrl: './otp-verification.component.html',
  styleUrl: './otp-verification.component.css'
})
export class OTPVerificationComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);
  private translate = inject(TranslateService);
  private langService = inject(LanguageService);

  email = '';
  emailSent = false; // whether OTP email was actually delivered
  isLoading = signal(false);
  isResending = signal(false);
  errorMsg = signal('');
  successMsg = signal('');
  warningMsg = signal('');
  resendCooldown = signal(0);
  resendLimitReached = signal(false);

  currentLang = this.langService.currentLang;
  dir = computed(() => this.currentLang() === 'ar' ? 'rtl' : 'ltr');

  private timerInterval: any;

  form = this.fb.group({
    code: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]]
  });

  ngOnInit() {
    this.email = sessionStorage.getItem('ins_otp_email') || '';
    if (!this.email) {
      this.router.navigate(['/login']);
      return;
    }
    this.emailSent = sessionStorage.getItem('ins_otp_email_sent') === 'true';
    if (this.emailSent) {
      this.successMsg.set(this.translate.instant('OTP.SUCCESS_SENT'));
    } else {
      this.warningMsg.set(this.translate.instant('OTP.EMAIL_FAILED_WARNING') || `Email delivery failed. Your code was generated — check the server terminal.`);
    }
  }

  ngOnDestroy() {
    this.clearTimer();
  }

  setLanguage(lang: string) {
    this.langService.use(lang);
  }

  onSubmit() {
    if (this.form.invalid) {
      this.errorMsg.set(this.translate.instant('OTP.ERR_EMPTY'));
      return;
    }

    this.isLoading.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');
    this.warningMsg.set('');


    const code = this.form.value.code!;

    this.auth.verifyOtp(this.email, code).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        sessionStorage.removeItem('ins_otp_email');
        if (res.preferred_language) {
          this.langService.use(res.preferred_language);
        }
        if (res.first_login) {
          this.router.navigate(['/change-password']);
        } else {
          if (res.role === 'COMPANY_CONTACT') {
            this.router.navigate(['/portal/home']);
          } else {
            this.router.navigate(['/admin/dashboard']);
          }
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMsg.set(err.error?.detail || this.translate.instant('LOGIN.ERR_LOGIN'));
      }
    });
  }

  onResend() {
    if (this.resendCooldown() > 0 || this.resendLimitReached()) {
      return;
    }

    this.isResending.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');
    this.warningMsg.set('');

    this.auth.requestOtp(this.email).subscribe({
      next: (res: any) => {
        this.isResending.set(false);
        if (res.email_sent === false) {
          this.warningMsg.set(this.translate.instant('OTP.EMAIL_FAILED_WARNING') || `Email delivery failed. Check the server terminal for the code.`);
        } else {
          this.successMsg.set(this.translate.instant('OTP.SUCCESS_SENT'));
        }
        this.startCooldown();
      },
      error: (err) => {
        this.isResending.set(false);
        const detail = err.error?.detail || '';
        this.errorMsg.set(detail || this.translate.instant('LOGIN.ERR_LOGIN'));
        if (err.status === 429 || detail.includes('limite') || detail.includes('limit')) {
          this.resendLimitReached.set(true);
        }
      }
    });
  }

  private startCooldown() {
    this.resendCooldown.set(60);
    this.clearTimer();
    this.timerInterval = setInterval(() => {
      this.resendCooldown.update(seconds => {
        if (seconds <= 1) {
          this.clearTimer();
          return 0;
        }
        return seconds - 1;
      });
    }, 1000);
  }

  private clearTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  get codeControl() {
    return this.form.get('code');
  }
}
