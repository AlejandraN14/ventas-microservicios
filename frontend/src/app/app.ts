import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ProductosService } from './services/productos';
import { PagosService } from './services/pagos';
import { UsuariosService } from './services/usuarios';
import { CarritoService } from './services/carrito';

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
  mensajeSesion: string = '';
  usuario: any = null;
  modoAuth: 'login' | 'registro' = 'login';

  nombreRegistro: string = '';
  emailAuth: string = '';
  passwordAuth: string = '';

  numeroTarjeta: string = '';
  mesVencimiento: number | null = null;
  anioVencimiento: number | null = null;
  cvv: string = '';
  nombreTitular: string = '';
  email: string = '';

  mostrarComprobante: boolean = false;
  comprobante: any = null;
  mostrarFormPago: boolean = false;



  constructor(
    private productosService: ProductosService,
    private pagosService: PagosService,
    private usuariosService: UsuariosService,
    private carritoService: CarritoService,
    private cdr: ChangeDetectorRef
  ) {}
  

  ngOnInit(): void {
    this.productosService.obtenerProductos().subscribe(data => {
      this.productos = data;
      this.cdr.detectChanges();
      console.log(data);
    });
  }

  autenticar(): void {
    this.mensajeSesion = '';

    const solicitud = this.modoAuth === 'registro'
      ? this.usuariosService.registrar(this.nombreRegistro, this.emailAuth, this.passwordAuth)
      : this.usuariosService.login(this.emailAuth, this.passwordAuth);

    solicitud.subscribe({
      next: (usuario) => {
        this.usuario = usuario;
        this.mensajeSesion = this.modoAuth === 'registro'
          ? 'Usuario registrado correctamente'
          : 'Sesion iniciada correctamente';
        this.passwordAuth = '';
        this.cargarCarrito();
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.mensajeSesion = error?.error?.detail || 'No fue posible autenticar el usuario';
        this.cdr.detectChanges();
      }
    });
  }

  cerrarSesion(): void {
    this.usuario = null;
    this.carrito = [];
    this.total = 0;
    this.mensajeSesion = 'Sesion cerrada';
    this.cdr.detectChanges();
  }

  cargarCarrito(): void {
    if (!this.usuario?.id) {
      return;
    }

    this.carritoService.obtener(this.usuario.id).subscribe(data => {
      this.carrito = data;
      this.calcularTotal();
      this.cdr.detectChanges();
    });
  }

  agregarAlCarrito(producto: any): void {
    if (!this.usuario?.id) {
      this.mensajeSesion = 'Debes iniciar sesion antes de agregar productos';
      this.cdr.detectChanges();
      return;
    }

    this.carritoService.agregar(this.usuario.id, producto.id).subscribe(data => {
      this.carrito = data;
      this.calcularTotal();
      this.cdr.detectChanges();
    });
  }

  eliminarDelCarrito(item: any): void{
    if (!this.usuario?.id) {
      return;
    }

    this.carritoService.eliminar(this.usuario.id, item.id).subscribe(data => {
      this.carrito = data;
      this.calcularTotal();
      this.cdr.detectChanges();
    });
  }

  calcularTotal(): void {
    this.total = this.carrito.reduce((suma, item) => suma + item.subtotal, 0)
  }

  getProductIcon(nombre: string): string {
    const n = nombre.toLowerCase();
    if (n.includes('notebook') || n.includes('laptop') || n.includes('computador')) return '💻';
    if (n.includes('mouse') || n.includes('raton')) return '🖱️';
    if (n.includes('teclado')) return '⌨️';
    if (n.includes('audifono') || n.includes('auricular') || n.includes('headphone')) return '🎧';
    if (n.includes('silla') || n.includes('chair')) return '🪑';
    if (n.includes('monitor') || n.includes('pantalla')) return '🖥️';
    if (n.includes('disco') || n.includes('ssd') || n.includes('hdd') || n.includes('pendrive')) return '💾';
    if (n.includes('camara') || n.includes('webcam')) return '📷';
    if (n.includes('impresora')) return '🖨️';
    if (n.includes('celular') || n.includes('telefono') || n.includes('movil')) return '📱';
    if (n.includes('tablet') || n.includes('ipad')) return '📟';
    if (n.includes('cable') || n.includes('cargador')) return '🔌';
    return '📦';
  }

  getProductColor(nombre: string): string {
    const n = nombre.toLowerCase();
    if (n.includes('notebook') || n.includes('laptop') || n.includes('computador'))
      return 'linear-gradient(145deg, #2d3a8c 0%, #4a5fc1 100%)';
    if (n.includes('mouse') || n.includes('raton'))
      return 'linear-gradient(145deg, #8b1a4a 0%, #c2436e 100%)';
    if (n.includes('teclado'))
      return 'linear-gradient(145deg, #0b5e6e 0%, #1a8fa3 100%)';
    if (n.includes('audifono') || n.includes('auricular'))
      return 'linear-gradient(145deg, #1a6b3a 0%, #2ea055 100%)';
    if (n.includes('silla') || n.includes('chair'))
      return 'linear-gradient(145deg, #7a3b00 0%, #b85c00 100%)';
    if (n.includes('monitor') || n.includes('pantalla'))
      return 'linear-gradient(145deg, #3d1f8a 0%, #6241c5 100%)';
    if (n.includes('disco') || n.includes('ssd') || n.includes('hdd'))
      return 'linear-gradient(145deg, #1f4e6b 0%, #2d7aad 100%)';
    if (n.includes('celular') || n.includes('telefono'))
      return 'linear-gradient(145deg, #1b5e3b 0%, #267a52 100%)';
    return 'linear-gradient(145deg, #7a5c00 0%, #b88a00 100%)';
  }

  decrementarDelCarrito(item: any): void {
    if (!this.usuario?.id) return;

    if (item.cantidad <= 1) {
      this.carritoService.eliminar(this.usuario.id, item.id).subscribe(data => {
        this.carrito = data;
        this.calcularTotal();
        this.cdr.detectChanges();
      });
    } else {
      this.carritoService.eliminar(this.usuario.id, item.id).subscribe(() => {
        this.carritoService.agregar(this.usuario.id, item.producto.id, item.cantidad - 1).subscribe(data => {
          this.carrito = data;
          this.calcularTotal();
          this.cdr.detectChanges();
        });
      });
    }
  }

  cerrarComprobante(): void {
    this.mostrarComprobante = false;
    this.comprobante = null;
    this.mostrarFormPago = false;
    this.numeroTarjeta = '';
    this.mesVencimiento = null;
    this.anioVencimiento = null;
    this.cvv = '';
    this.nombreTitular = '';
    this.email = '';
    this.mensajePago = '';
    this.cdr.detectChanges();
  }

  imprimirComprobante(): void {
    window.print();
  }

  pagar(): void {

  if (!this.usuario?.id) {
    this.mensajePago = 'Debes iniciar sesion antes de pagar';
    this.cdr.detectChanges();
    return;
  }

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
    this.usuario.id,
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

      if (estado === 'PAGADO') {
        const itemsCompra = [...this.carrito];
        this.comprobante = {
          numero: respuesta?.data?.id_pago,
          referencia: respuesta?.data?.external_reference,
          mpPaymentId: respuesta?.data?.mp_payment_id,
          monto: this.total,
          metodoPago: this.metodoPago,
          fecha: new Date(),
          email: this.email,
          titular: this.nombreTitular,
          items: itemsCompra
        };
        this.mostrarComprobante = true;
        this.carrito = [];
        this.total = 0;
        this.mensajePago = '';

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
