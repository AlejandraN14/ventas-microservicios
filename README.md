# Sistema de Ventas Online con Microservicios

Proyecto de evaluacion basado en una arquitectura de microservicios para una tienda online. Permite registrar usuarios, iniciar sesion, visualizar productos, administrar un carrito de compras y procesar pagos con tarjeta mediante un microservicio especializado.

## Arquitectura

El sistema se compone de los siguientes servicios:

- **Frontend:** Angular, interfaz de tienda, registro/login, catalogo, carrito y pago.
- **Backend:** FastAPI, API REST principal para usuarios, productos, carrito, ventas e integracion con pagos.
- **Microservicio de pagos:** FastAPI, servicio `app-pagos` integrado con Mercado Pago.
- **Base de datos:** PostgreSQL para persistir usuarios, productos, carrito y ventas.

## Puertos locales

- Frontend: <http://localhost:4200>
- Backend: <http://localhost:8001>
- Swagger backend: <http://localhost:8001/docs>
- Microservicio de pagos: <http://localhost:8002/docs>
- PostgreSQL: `localhost:5432`

## Funcionalidades

- Registro de usuario.
- Inicio de sesion.
- Visualizacion de productos persistidos en base de datos.
- Carrito de compras asociado al usuario.
- Proceso de pago con credito o debito.
- Integracion entre backend y microservicio `app-pagos`.
- Registro de ventas en PostgreSQL.
- Contenedores Docker para frontend, backend, pagos y base de datos.
- Pipeline GitHub Actions para build, push a AWS ECR y despliegue en ECS.

## Ejecucion local con Docker

```bash
docker compose up --build
```

Luego abrir:

```text
http://localhost:4200
```

## Variables de entorno

El backend usa:

```text
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ventasdb
```

El microservicio `app-pagos` requiere credenciales de Mercado Pago:

```text
MP_ACCESS_TOKEN=...
MP_PUBLIC_KEY=...
MP_SUCCESS_URL=...
MP_FAILURE_URL=...
MP_PENDING_URL=...
MP_WEBHOOK_URL=...
```

## CI/CD en AWS

El workflow esta en:

```text
.github/workflows/deploy-aws.yml
```

El pipeline realiza:

1. Checkout del repositorio.
2. Configuracion de credenciales AWS.
3. Login en Amazon ECR.
4. Build de imagenes Docker para `frontend`, `backend` y `app-pagos`.
5. Push de imagenes a ECR.
6. Render de task definitions.
7. Deploy automatico a servicios ECS.

Secrets requeridos en GitHub:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCOUNT_ID
```

Variables requeridas en GitHub:

```text
AWS_REGION
ECS_CLUSTER
```

Repositorios ECR esperados:

```text
ventas-frontend
ventas-backend
ventas-app-pagos
```

Servicios ECS esperados:

```text
ventas-frontend-service
ventas-backend-service
ventas-app-pagos-service
```

## Infraestructura AWS

Los archivos base de task definitions estan en:

```text
aws/task-definition-frontend.json
aws/task-definition-backend.json
aws/task-definition-app-pagos.json
```

Antes del despliegue real, reemplazar `ACCOUNT_ID` y `REGION` o configurar el render desde el pipeline/servicios existentes. Para produccion se recomienda usar AWS RDS para PostgreSQL y AWS Systems Manager Parameter Store o Secrets Manager para las credenciales de Mercado Pago.

## Endpoints principales

- `POST /usuarios/registro`
- `POST /usuarios/login`
- `GET /productos`
- `POST /productos`
- `GET /usuarios/{usuario_id}/carrito`
- `POST /usuarios/{usuario_id}/carrito`
- `DELETE /usuarios/{usuario_id}/carrito/{item_id}`
- `DELETE /usuarios/{usuario_id}/carrito`
- `POST /procesar-pagos`
- `GET /ventas`

Ejemplo para crear un producto desde Swagger o Postman:

```json
{
  "nombre": "Monitor 27 pulgadas",
  "precio": 180000,
  "descripcion": "Monitor Full HD para trabajo y juegos"
}
```

## Demo sugerida

1. Levantar el proyecto con Docker Compose.
2. Registrar un usuario desde Angular.
3. Iniciar sesion.
4. Agregar productos al carrito.
5. Completar datos de tarjeta de prueba.
6. Procesar pago.
7. Mostrar venta registrada en `GET /ventas`.
8. Hacer un cambio menor, subirlo a GitHub y mostrar la ejecucion del workflow CI/CD.
