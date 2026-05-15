import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UsuariosService {
  private apiUrl = 'http://localhost:8001/usuarios';

  constructor(private http: HttpClient) {}

  registrar(nombre: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/registro`, { nombre, email, password });
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, { email, password });
  }
}
