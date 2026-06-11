import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const FILE_SERVICE_URL = 'http://localhost:8004';

@Injectable({ providedIn: 'root' })
export class ArchivosService {
  constructor(private http: HttpClient) {}

  subirArchivo(usuarioId: number, archivo: File, whatsapp?: string): Observable<any> {
    const form = new FormData();
    form.append('archivo', archivo);
    if (whatsapp) form.append('whatsapp', whatsapp);
    return this.http.post(`${FILE_SERVICE_URL}/archivos/${usuarioId}/subir`, form);
  }

  listarArchivos(usuarioId: number): Observable<any[]> {
    return this.http.get<any[]>(`${FILE_SERVICE_URL}/archivos/${usuarioId}`);
  }

  consultarEspacio(usuarioId: number): Observable<any> {
    return this.http.get(`${FILE_SERVICE_URL}/archivos/${usuarioId}/espacio`);
  }

  eliminarArchivo(usuarioId: number, nombre: string): Observable<any> {
    return this.http.delete(`${FILE_SERVICE_URL}/archivos/${usuarioId}/${nombre}`);
  }
}
