import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class CarritoService {
  private apiUrl = 'http://3.133.148.130:8001/usuarios';

  constructor(private http: HttpClient) {}

  obtener(usuarioId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/${usuarioId}/carrito`);
  }

  agregar(usuarioId: number, productoId: number, cantidad = 1): Observable<any> {
    return this.http.post(`${this.apiUrl}/${usuarioId}/carrito`, {
      producto_id: productoId,
      cantidad,
    });
  }

  eliminar(usuarioId: number, itemId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${usuarioId}/carrito/${itemId}`);
  }

  vaciar(usuarioId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${usuarioId}/carrito`);
  }
}
