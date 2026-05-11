import { TestBed } from '@angular/core/testing';

import { Pagos } from './pagos';

describe('Pagos', () => {
  let service: Pagos;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Pagos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
