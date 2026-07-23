import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  templateUrl: './change-password.html',
})
export class ChangePassword {
  private authService = inject(AuthService);

  currentPassword = '';
  newPassword = '';
  confirmPassword = '';
  
  isSaving = false;
  successMessage = '';
  errorMessage = '';

  showCurrentPassword = false;
  showNewPassword = false;
  showConfirmPassword = false;

  get isLengthValid(): boolean {
    return this.newPassword.length >= 8;
  }

  get hasUppercase(): boolean {
    return /[A-Z]/.test(this.newPassword);
  }

  get hasLowercase(): boolean {
    return /[a-z]/.test(this.newPassword);
  }

  get hasNumber(): boolean {
    return /[0-9]/.test(this.newPassword);
  }

  get hasSpecial(): boolean {
    return /[^A-Za-z0-9]/.test(this.newPassword);
  }

  get passwordStrength(): number {
    let score = 0;
    if (this.newPassword.length > 0) score += 20;
    if (this.isLengthValid) score += 20;
    if (this.hasUppercase) score += 20;
    if (this.hasLowercase) score += 20;
    if (this.hasNumber || this.hasSpecial) score += 20;
    return score;
  }

  get strengthLabel(): string {
    if (this.passwordStrength < 40) return 'Weak';
    if (this.passwordStrength < 80) return 'Medium';
    return 'Strong';
  }

  get strengthColor(): string {
    if (this.passwordStrength < 40) return 'bg-danger';
    if (this.passwordStrength < 80) return 'bg-warning';
    return 'bg-success';
  }

  get isPasswordValid(): boolean {
    return this.isLengthValid && this.hasUppercase && this.hasLowercase && this.hasNumber && this.hasSpecial;
  }

  get passwordMatch(): boolean {
    return this.newPassword.length > 0 && this.newPassword === this.confirmPassword;
  }

  get canSubmit(): boolean {
    return this.currentPassword.length > 0 && 
           this.isPasswordValid && 
           this.passwordMatch && 
           !this.isSaving;
  }

  toggleCurrentPassword() {
    this.showCurrentPassword = !this.showCurrentPassword;
  }

  toggleNewPassword() {
    this.showNewPassword = !this.showNewPassword;
  }

  toggleConfirmPassword() {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  submit() {
    if (!this.canSubmit) return;

    this.isSaving = true;
    this.successMessage = '';
    this.errorMessage = '';

    this.authService.updateProfilePassword({
      current_password: this.currentPassword,
      new_password: this.newPassword
    }).subscribe({
      next: () => {
        this.isSaving = false;
        this.successMessage = 'Your password has been successfully updated.';
        this.currentPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
      },
      error: (err) => {
        this.isSaving = false;
        this.errorMessage = err.error?.detail || 'Failed to update password. Please check your current password.';
      }
    });
  }
}
