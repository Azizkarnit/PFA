import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SystemSettingsService, SystemSettings as Settings } from '../../../core/services/system-settings.service';

@Component({
  selector: 'app-system-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './system-settings.html',
  styles: ``,
})
export class SystemSettings implements OnInit {
  private settingsService = inject(SystemSettingsService);

  settings: Settings = {
    code_expiration: 5,
    max_signin_attempts: 3,
    lock_duration: 24,
    password_only_duration: 1,
    default_language: 'French',
    email_provider: 'Brevo'
  };

  isSaving = false;
  successMessage = '';
  errorMessage = '';

  ngOnInit() {
    this.loadSettings();
  }

  loadSettings() {
    this.settingsService.getSettings().subscribe({
      next: (res) => {
        this.settings = res;
      },
      error: (err) => {
        console.error('Error loading system settings', err);
        this.errorMessage = 'Failed to load system settings.';
      }
    });
  }

  saveSettings() {
    this.isSaving = true;
    this.successMessage = '';
    this.errorMessage = '';

    this.settingsService.updateSettings(this.settings).subscribe({
      next: (res) => {
        this.settings = res;
        this.isSaving = false;
        this.successMessage = 'Settings saved successfully!';
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (err) => {
        console.error('Error saving system settings', err);
        this.isSaving = false;
        this.errorMessage = 'Failed to save settings. Please try again.';
      }
    });
  }
}
