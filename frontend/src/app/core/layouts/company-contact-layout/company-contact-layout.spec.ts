import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompanyContactLayout } from './company-contact-layout';

describe('CompanyContactLayout', () => {
  let component: CompanyContactLayout;
  let fixture: ComponentFixture<CompanyContactLayout>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompanyContactLayout],
    }).compileComponents();

    fixture = TestBed.createComponent(CompanyContactLayout);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
