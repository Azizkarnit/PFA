import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Auth } from '../../services/auth';

@Component({
  selector: 'app-otp-verify',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './otp-verify.html',
  styleUrl: './otp-verify.css'
})
export class OtpVerify implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(Auth);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  email = '';
  isLoading = false;
  error = '';

  otpForm = this.fb.group({
    digit1: ['', Validators.required],
    digit2: ['', Validators.required],
    digit3: ['', Validators.required],
    digit4: ['', Validators.required],
    digit5: ['', Validators.required],
    digit6: ['', Validators.required]
  });

  ngOnInit() {
    this.email = this.route.snapshot.queryParamMap.get('email') || '';
    if (!this.email) {
      this.router.navigate(['/auth/login']);
    }
  }

  onInput(event: any, nextFieldId: string | null) {
    if (event.target.value && nextFieldId) {
      document.getElementById(nextFieldId)?.focus();
    }
  }

  onKeyDown(event: any, prevFieldId: string | null) {
    if (event.key === 'Backspace' && !event.target.value && prevFieldId) {
      document.getElementById(prevFieldId)?.focus();
    }
  }

  onSubmit() {
    if (this.otpForm.invalid) return;

    this.isLoading = true;
    this.error = '';

    const code = Object.values(this.otpForm.value).join('');

    this.authService.verifyOtp({ email: this.email, code }).subscribe({
      next: (res) => {
        this.isLoading = false;
        if (res.first_login) {
          this.router.navigate(['/auth/change-password']);
        } else {
          this.router.navigate(['/']); // Dashboard
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.error = err.error?.detail || 'Verification failed. Please try again.';
      }
    });
  }
}
