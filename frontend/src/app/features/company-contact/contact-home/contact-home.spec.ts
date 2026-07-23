import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ContactHome } from './contact-home';

describe('ContactHome', () => {
  let component: ContactHome;
  let fixture: ComponentFixture<ContactHome>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ContactHome],
    }).compileComponents();

    fixture = TestBed.createComponent(ContactHome);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
