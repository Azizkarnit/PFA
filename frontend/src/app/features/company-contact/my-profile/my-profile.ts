import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PortalService, PortalProfile, PortalProfileUpdate } from '../../../core/services/portal.service';

@Component({
  selector: 'app-my-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  templateUrl: './my-profile.html',
})
export class MyProfile implements OnInit {
  private portalService = inject(PortalService);

  profile: PortalProfile | null = null;
  isLoading = true;
  isSaving = false;
  successMessage = '';
  errorMessage = '';

  ngOnInit() {
    this.loadProfile();
  }

  loadProfile() {
    this.isLoading = true;
    this.portalService.getProfile().subscribe({
      next: (data) => {
        this.profile = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Failed to load profile', err);
        this.errorMessage = 'Failed to load profile details.';
        this.isLoading = false;
      }
    });
  }

  saveChanges() {
    if (!this.profile) return;
    
    this.isSaving = true;
    this.successMessage = '';
    this.errorMessage = '';

    const updateData: PortalProfileUpdate = {
      first_name: this.profile.first_name,
      last_name: this.profile.last_name,
      position: this.profile.position,
      preferred_language: this.profile.preferred_language,
    };

    this.portalService.updateProfile(updateData).subscribe({
      next: (updatedProfile) => {
        this.profile = updatedProfile;
        this.isSaving = false;
        this.successMessage = 'Profile updated successfully.';
        
        // Hide success message after 3 seconds
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      },
      error: (err) => {
        console.error('Failed to save profile', err);
        this.isSaving = false;
        this.errorMessage = 'Failed to save changes. Please try again.';
      }
    });
  }
}
