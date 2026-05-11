import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class PagosService {

  private apiUrl = 'http://127.0.0.1:8001/procesar-pagos';

  constructor(private http: HttpClient) {}
  procesarPago(monto: number): Observable<any> {
    return this.http.post(this.apiUrl,{ monto});
  }
}
