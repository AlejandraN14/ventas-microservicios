import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductosService } from './services/productos';
import { PagosService } from './services/pagos';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  productos: any[] = [];
  carrito: any[] = [];
  total:number = 0;

   mensajePago: string = '';


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

    this.pagosService.procesarPago(this.total).subscribe({
      next: (respuesta) => {console.log(respuesta);

        this.mensajePago = respuesta.message;
        this.carrito = [];
        this.total = 0;

        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error(error);
        this.mensajePago = 'Error al procesar el pago';

        this.cdr.detectChanges();
      }

    });
  }
  
}