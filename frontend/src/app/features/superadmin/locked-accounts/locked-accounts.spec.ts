import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LockedAccounts } from './locked-accounts';

describe('LockedAccounts', () => {
  let component: LockedAccounts;
  let fixture: ComponentFixture<LockedAccounts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LockedAccounts],
    }).compileComponents();

    fixture = TestBed.createComponent(LockedAccounts);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
