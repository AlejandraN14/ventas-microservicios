import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class CarritoService {
  constructor(private http: HttpClient) {}

  obtener(usuarioId: number): Observable<any> {
    return this.http.get(`${getApiBaseUrl()}/usuarios/${usuarioId}/carrito`);
  }

  agregar(usuarioId: number, productoId: number, cantidad = 1): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/usuarios/${usuarioId}/carrito`, {
      producto_id: productoId,
      cantidad,
    });
  }

  eliminar(usuarioId: number, itemId: number): Observable<any> {
    return this.http.delete(`${getApiBaseUrl()}/usuarios/${usuarioId}/carrito/${itemId}`);
  }

  vaciar(usuarioId: number): Observable<any> {
    return this.http.delete(`${getApiBaseUrl()}/usuarios/${usuarioId}/carrito`);
  }
}
