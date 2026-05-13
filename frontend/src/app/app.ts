import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ProductosService } from './services/productos';
import { PagosService } from './services/pagos';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  productos: any[] = [];
  carrito: any[] = [];
  total:number = 0;
  metodoPago: string = 'debito';
  mensajePago: string = '';

  numeroTarjeta: string = '';
  mesVencimiento: number | null = null;
  anioVencimiento: number | null = null;
  cvv: string = '';
  nombreTitular: string = '';
  email: string = '';



  constructor(
    private productosService: ProductosService,
    private pagosService: PagosService,
    private cdr: ChangeDetectorRef
  ) {}
  

  ngOnInit(): void {
    this.productosService.obtenerProductos().subscribe(data => {
      this.productos = data;
      this.cdr.detectChanges();
      console.log(data);
    });
  }

  agregarAlCarrito(producto: any): void {
    this.carrito.push(producto);
    this.calcularTotal();
  }

  eliminarDelCarrito(index: number): void{
    this.carrito.splice(index, 1);
    this.calcularTotal();
  }

  calcularTotal(): void {
    this.total = this.carrito.reduce((suma, item) => suma + item.precio, 0)
  }

  pagar(): void {

  if (this.carrito.length === 0 || this.total <= 0) {
    this.mensajePago = 'Debes agregar productos al carrito antes de pagar';
    this.cdr.detectChanges();
    return;
  }

  if (
    !this.numeroTarjeta ||
    this.mesVencimiento === null ||
    this.anioVencimiento === null ||
    !this.cvv ||
    !this.nombreTitular ||
    !this.email
  ) {
    this.mensajePago = 'Debes completar todos los datos de la tarjeta';
    this.cdr.detectChanges();
    return;
  }

  this.mensajePago = 'Procesando pago...';
  this.cdr.detectChanges();

  this.pagosService.procesarPago(
    this.total,
    this.metodoPago,
    this.numeroTarjeta,
    this.mesVencimiento,
    this.anioVencimiento,
    this.cvv,
    this.nombreTitular,
    this.email
  ).subscribe({
    next: (respuesta) => {
      console.log('Respuesta del pago:', respuesta);

      if (respuesta?.detail) {
        if (Array.isArray(respuesta.detail)) {
          this.mensajePago = respuesta.detail
            .map((error: any) => error.msg)
            .join(' | ');
        } else {
          this.mensajePago = respuesta.detail;
        }

        this.cdr.detectChanges();
        return;
      }

      const estado = respuesta?.data?.estado;
      const mensaje = respuesta?.message;

      if (estado === 'PAGADO') {
        this.mensajePago = 'Pago aprobado correctamente';
        this.carrito = [];
        this.total = 0;

      } else if (estado === 'RECHAZADO') {
        this.mensajePago = 'Pago rechazado';

      } else if (estado === 'PENDIENTE') {
        this.mensajePago = 'Pago pendiente de confirmación';

      } else if (estado === 'CANCELADO') {
        this.mensajePago = 'Pago cancelado';

      } else if (estado === 'EXPIRADO') {
        this.mensajePago = ' Pago expirado';  

      } else {
        this.mensajePago = respuesta?.message || 'Respuesta desconocida del pago';
      }

      this.cdr.detectChanges();
    },

    error: (error) => {
      console.error('Error al procesar pago:', error);

      if (error?.error?.detail) {
        if (Array.isArray(error.error.detail)) {
          this.mensajePago = error.error.detail
            .map((e: any) => e.msg)
            .join(' | ');
        } else {
          this.mensajePago = error.error.detail;
        }
      } else {
        this.mensajePago = 'Error al procesar el pago';
      }

      this.cdr.detectChanges();
    }
  });
}
  
}