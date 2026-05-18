import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class ProductosService {

  constructor (private http: HttpClient) {}

  obtenerProductos(): Observable<any> {
    return this.http.get(`${getApiBaseUrl()}/productos`);
  }
}
