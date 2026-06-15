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
    nombreTitular: string,
    email: string,
    itemsCarrito: any[] = []
  ): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/procesar-pagos`, {
      usuario_id: usuarioId,
      monto: monto,
      metodo_pago: metodoPago,
      nombre_titular: nombreTitular,
      email: email,
      items_carrito: itemsCarrito,
    });
  }
}
