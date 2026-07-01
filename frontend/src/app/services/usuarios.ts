import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBaseUrl } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class UsuariosService {
  constructor(private http: HttpClient) {}

  registrar(nombre: string, email: string, password: string): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/usuarios/registro`, { nombre, email, password });
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/usuarios/login`, { email, password });
  }

  verificar(email: string, codigo: string): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/usuarios/verificar`, { email, codigo });
  }

  logout(usuarioId: number, email: string): Observable<any> {
    return this.http.post(`${getApiBaseUrl()}/usuarios/logout`, { usuario_id: usuarioId, email });
  }
}
