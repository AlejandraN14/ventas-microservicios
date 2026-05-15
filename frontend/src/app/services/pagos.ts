import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class PagosService {

  private apiUrl = 'http://localhost:8001/procesar-pagos';

  constructor(private http: HttpClient) {}
  
  procesarPago(
    usuarioId: number,
    monto: number,
    metodoPago: string,
    numeroTarjeta: string,
    mesVencimiento: number,
    anioVencimiento: number,
    cvv: string,
    nombreTitular: string,
    email: string
  ): Observable<any> {
    return this.http.post(this.apiUrl, {
      usuario_id: usuarioId,
      monto: monto,
      metodo_pago: metodoPago,
      numero_tarjeta: numeroTarjeta,
      mes_vencimiento: mesVencimiento,
      anio_vencimiento: anioVencimiento,
      cvv: cvv,
      nombre_titular: nombreTitular,
      email: email
      });
  }
}
