# Tarjetas Guardadas - DEPRECATED

Este módulo ha sido eliminado en favor de pagos directos sin guardar tarjetas.

## Cambios Realizados

### Rutas Eliminadas:
- `POST /tarjetas/guardar` - Guardar tarjeta
- `GET /tarjetas/usuario/{id_usuario}` - Listar tarjetas
- `POST /tarjetas/marcar-predeterminada` - Marcar como default
- `DELETE /tarjetas/{id}` - Eliminar tarjeta
- `POST /tarjetas/pagar` - Pago con tarjeta guardada

### Nueva Ruta de Pago:
- `POST /pagos/directo/procesar` - Pago directo sin guardar tarjeta

### Modelos Eliminados:
- `MpCustomer` - Customer de Mercado Pago
- `TarjetaGuardada` - Tarjeta guardada en BD

### Schemas Eliminados:
- `TarjetaGuardarRequest/Response`
- `PagoConTarjetaGuardadaRequest/Response`
- Todos los schemas de tarjeta

## Migración de App Móvil

La app móvil debe usar el nuevo endpoint:
```
POST /pagos/directo/procesar
```

Con el payload:
```json
{
    "id_usuario": 1,
    "numero_tarjeta": "4168818844447115",
    "mes_vencimiento": 11,
    "anio_vencimiento": 2030,
    "cvv": "123",
    "nombre_titular": "APRO",
    "email": "usuario@test.com",
    "descripcion": "Pago de suscripción",
    "monto": 100.00
}
```

La respuesta incluye `id_pago` que debe usarse para polling del estado:
```
GET /pagos/{id_pago}/estado
```

## Estados de Pago

Estados que devuelve la API:
- `PENDIENTE` - Pago en proceso
- `PAGADO` - Pago aprobado
- `RECHAZADO` - Pago rechazado
- `ANULADO` - Pago cancelado

## Timeout

La app móvil debe esperar máximo 2 minutos (120 segundos) para obtener la respuesta final.
Después de ese tiempo, se debe mostrar un error de timeout.

Tarjetas de prueba y estados especiales:
https://www.mercadopago.com.cl/developers/es/docs/checkout-api/test-cards
