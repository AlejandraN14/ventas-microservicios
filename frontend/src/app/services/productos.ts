import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ProductosService {

  private apiUrl = 'http://127.0.0.1:8001/productos';

  constructor (private http: HttpClient) {}

  obtenerProductos(): Observable<any> {
    return this.http.get(this.apiUrl);
  }
}
