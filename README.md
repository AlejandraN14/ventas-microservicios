\# Sistema de Ventas Online con Microservicios



Proyecto desarrollado para evaluación de microservicios, Docker, CI/CD y AWS.



\## Arquitectura



El sistema está compuesto por 3 servicios principales:



\- Frontend: Angular

\- Backend: FastAPI

\- Microservicio de pagos: app-pagos



\## Puertos



\- Frontend: http://localhost:4200

\- Backend: http://localhost:8001

\- app-pagos: http://localhost:8002/docs



\## Levantar proyecto con Docker



```bash

docker compose up --build

