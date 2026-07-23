import { Component, inject } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { Sidebar } from '../../../shared/components/sidebar/sidebar';
import { Topbar } from '../../../shared/components/topbar/topbar';
import { filter } from 'rxjs';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, Sidebar, Topbar],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css',
})
export class AdminLayout {
  isMobileMenuOpen = false;
  private router = inject(Router);
  private titleService = inject(Title);
  private currentUrl = '';

  constructor() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.currentUrl = event.urlAfterRedirects;
      this.closeMobileMenu();
      const pageTitle = this.getPageTitle();
      this.titleService.setTitle(`${pageTitle} | INS Survey Platform`);
    });
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  closeMobileMenu() {
    this.isMobileMenuOpen = false;
  }

  getPageTitle(): string {
    if (this.currentUrl.includes('/admin/dashboard')) return 'Dashboard';
    if (this.currentUrl.includes('/admin/administrators')) return 'Administrators';
    if (this.currentUrl.includes('/admin/users')) return 'Users';
    if (this.currentUrl.includes('/admin/locked-accounts')) return 'Locked Accounts';
    if (this.currentUrl.includes('/admin/companies')) return 'Companies';
    if (this.currentUrl.includes('/admin/contacts')) return 'Contacts';
    if (this.currentUrl.includes('/admin/surveys')) return 'Surveys';
    if (this.currentUrl.includes('/admin/audit-logs')) return 'Audit Logs';
    if (this.currentUrl.includes('/admin/system-settings')) return 'System Settings';
    return 'INS Survey Platform';
  }
}
