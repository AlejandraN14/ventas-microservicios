import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class PagosService {

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
    return this.http.post(`${getApiBaseUrl()}/procesar-pagos`, {
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
