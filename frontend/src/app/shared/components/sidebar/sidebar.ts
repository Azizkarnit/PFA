import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

import { TranslatePipe } from '@ngx-translate/core';

import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  private authService = inject(AuthService);
  private router = inject(Router);

  get role(): string | null {
    const user = this.authService.getCurrentUser();
    return user ? user.role : null;
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
