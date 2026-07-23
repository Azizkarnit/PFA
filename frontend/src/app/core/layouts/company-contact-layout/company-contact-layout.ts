import { Component, inject } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd, ChildrenOutletContexts, RouterLink, RouterLinkActive } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { Topbar } from '../../../shared/components/topbar/topbar';
import { filter } from 'rxjs';
import { trigger, transition, style, query, animate, group } from '@angular/animations';

export const routeAnimations = trigger('routeAnimations', [
  transition('* <=> *', [
    style({ position: 'relative' }),
    query(':enter, :leave', [
      style({
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        opacity: 0,
        transform: 'translateY(15px)'
      })
    ], { optional: true }),
    query(':enter', [
      style({ opacity: 0, transform: 'translateY(15px)' })
    ], { optional: true }),
    group([
      query(':leave', [
        animate('0.2s ease-in', style({ opacity: 0, transform: 'translateY(-15px)' }))
      ], { optional: true }),
      query(':enter', [
        animate('0.3s 0.2s ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ], { optional: true })
    ])
  ])
]);

@Component({
  selector: 'app-company-contact-layout',
  standalone: true,
  imports: [RouterOutlet, Topbar, CommonModule, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './company-contact-layout.html',
  styleUrl: './company-contact-layout.css',
  animations: [routeAnimations]
})
export class CompanyContactLayout {
  isMobileMenuOpen = false;
  private router = inject(Router);
  private titleService = inject(Title);
  private contexts = inject(ChildrenOutletContexts);
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
    if (this.currentUrl.includes('/portal/home')) return 'Home';
    if (this.currentUrl.includes('/portal/survey')) return 'Survey Detail';
    if (this.currentUrl.includes('/portal/results')) return 'Results';
    if (this.currentUrl.includes('/portal/profile')) return 'My Profile';
    if (this.currentUrl.includes('/portal/change-password')) return 'Change Password';
    return 'INS Survey Platform';
  }

  getRouteAnimationData() {
    return this.contexts.getContext('primary')?.route?.snapshot?.url?.join('') || 'default';
  }
}
