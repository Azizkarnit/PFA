import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { NgApexchartsModule, ApexOptions } from 'ng-apexcharts';
import { DashboardService, DashboardStats } from '../../../core/services/dashboard.service';
import { AuthService } from '../../../core/services/auth.service';
import { CompanyService, Company } from '../../../core/services/company.service';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, RouterModule, TranslatePipe, NgApexchartsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
  providers: [DatePipe]
})
export class Dashboard implements OnInit {
  stats: DashboardStats | null = null;
  recentCompanies: Company[] = [];
  
  // Chart Configurations
  public sectorChartOptions: Partial<ApexOptions> = {};
  public statusChartOptions: Partial<ApexOptions> = {};
  public companiesGrowthChartOptions: Partial<ApexOptions> = {};
  public surveysGrowthChartOptions: Partial<ApexOptions> = {};
  public contactsGrowthChartOptions: Partial<ApexOptions> = {};

  private dashboardService = inject(DashboardService);
  private authService = inject(AuthService);
  private companyService = inject(CompanyService);
  
  get role(): string | null {
    const user = this.authService.getCurrentUser();
    return user ? user.role : null;
  }
  
  // Define distinct colors for the roles
  roleColors = ['#003866', '#006874', '#1E8E5A', '#D98A00', '#D32F2F', '#7B1FA2'];
  
  // Data for the SVG Donut chart
  donutSegments: any[] = [];

  ngOnInit(): void {
    this.dashboardService.getStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.calculateDonutChart();
        this.setupCharts();
      },
      error: (err) => {
        console.error('Error fetching dashboard stats', err);
      }
    });

    if (this.role !== 'SYSTEM_ADMINISTRATOR') {
      this.companyService.getCompanies(0, 5).subscribe({
        next: (data) => {
          this.recentCompanies = data.items;
        },
        error: (err) => console.error('Error fetching companies', err)
      });
    }
  }


  setupCharts(): void {
    if (!this.stats) return;

    // Sector Chart (Donut)
    const sectorLabels = this.stats.companies_by_sector.map(s => s.sector_name);
    const sectorData = this.stats.companies_by_sector.map(s => s.count);
    this.sectorChartOptions = {
      series: sectorData,
      chart: { type: 'donut', height: 350 },
      labels: sectorLabels,
      colors: this.roleColors,
      title: { text: 'Companies by Sector', align: 'left', style: { fontSize: '16px', fontWeight: 'bold' } },
      dataLabels: { enabled: false }
    };

    // Status Chart (Donut)
    const statusLabels = this.stats.companies_by_status.map(s => s.status);
    const statusData = this.stats.companies_by_status.map(s => s.count);
    this.statusChartOptions = {
      series: statusData,
      chart: { type: 'donut', height: 350 },
      labels: statusLabels,
      colors: ['#1E8E5A', '#D32F2F', '#D98A00'],
      title: { text: 'Company Status Breakdown', align: 'left', style: { fontSize: '16px', fontWeight: 'bold' } },
      dataLabels: { enabled: false }
    };

    // Companies Growth Chart (Area)
    const compGrowthLabels = this.stats.companies_growth.map(s => s.month);
    const compGrowthData = this.stats.companies_growth.map(s => s.count);
    this.companiesGrowthChartOptions = {
      series: [{ name: 'New Companies', data: compGrowthData }],
      chart: { type: 'area', height: 350, toolbar: { show: false } },
      xaxis: { categories: compGrowthLabels },
      title: { text: 'Companies Growth (Last 6 Months)', align: 'left', style: { fontSize: '16px', fontWeight: 'bold' } },
      colors: ['#003866'],
      stroke: { curve: 'smooth' }
    };

    // Surveys Growth Chart (Bar)
    const surGrowthLabels = this.stats.surveys_growth.map(s => s.month);
    const surGrowthData = this.stats.surveys_growth.map(s => s.count);
    this.surveysGrowthChartOptions = {
      series: [{ name: 'New Surveys', data: surGrowthData }],
      chart: { type: 'bar', height: 350, toolbar: { show: false } },
      xaxis: { categories: surGrowthLabels },
      title: { text: 'Survey Creation Trends', align: 'left', style: { fontSize: '16px', fontWeight: 'bold' } },
      colors: ['#006874']
    };

    // Contacts Growth Chart (Area)
    const contactGrowthLabels = this.stats.contacts_growth.map(s => s.month);
    const contactGrowthData = this.stats.contacts_growth.map(s => s.count);
    this.contactsGrowthChartOptions = {
      series: [{ name: 'New Contacts', data: contactGrowthData }],
      chart: { type: 'area', height: 350, toolbar: { show: false } },
      xaxis: { categories: contactGrowthLabels },
      title: { text: 'Contacts Growth (Last 6 Months)', align: 'left', style: { fontSize: '16px', fontWeight: 'bold' } },
      colors: ['#D98A00'],
      stroke: { curve: 'smooth' }
    };
  }

  calculateDonutChart(): void {
    if (!this.stats || !this.stats.role_distribution) return;

    let currentOffset = 0;
    const radius = 60;
    const circumference = 2 * Math.PI * radius; // ~376.99
    
    // Sort so largest is first (optional, looks better)
    const sortedRoles = [...this.stats.role_distribution].sort((a, b) => b.percentage - a.percentage);

    this.donutSegments = sortedRoles.map((role, index) => {
      // SVG stroke-dasharray takes length of dash, length of gap.
      // E.g. [filled_length, remaining_length]
      const dash = (role.percentage / 100) * circumference;
      const gap = circumference - dash;
      const strokeDasharray = `${dash} ${gap}`;
      const strokeDashoffset = -currentOffset;
      
      // Advance offset for next segment
      currentOffset += dash;

      return {
        ...role,
        color: this.roleColors[index % this.roleColors.length],
        strokeDasharray,
        strokeDashoffset
      };
    });
    
    // Replace the original array to maintain order with new colors, or keep the sorted one
    this.stats.role_distribution = this.donutSegments;
  }
}

