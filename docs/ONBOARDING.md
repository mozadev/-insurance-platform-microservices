# 🚀 Onboarding Guide - Insurance Microservices Platform

Guía paso a paso para integrar nuevos miembros al equipo.

## 📅 Plan de Onboarding - Primera Semana

### Día 1: Bienvenida y Configuración

#### Mañana (9:00 AM - 12:00 PM)

**1. Bienvenida del Equipo (30 min)**
- Reunión con el Tech Lead
- Presentación del equipo en Slack
- Tour del repositorio y arquitectura

**2. Accesos y Credenciales (1 hora)**
- [ ] Cuenta de GitHub agregada a la organización
- [ ] Acceso a Slack channels:
  - `#insurance-platform-dev`
  - `#insurance-platform-alerts`
  - `#insurance-platform-general`
- [ ] Acceso a Jira/Linear para gestión de tareas
- [ ] Acceso a Confluence/Notion para documentación
- [ ] Credenciales AWS (IAM user con Developer role)

**3. Configuración del Entorno (1.5 horas)**
- [ ] Clonar repositorio
- [ ] Instalar herramientas (Python, Docker, AWS CLI, Terraform)
- [ ] Configurar AWS CLI
- [ ] Ejecutar `make setup`
- [ ] Verificar que todo funcione con `make test`

#### Tarde (2:00 PM - 5:00 PM)

**4. Lectura de Documentación (2 horas)**
- [ ] [README.md](../README.md) - Overview del proyecto
- [ ] [DEVELOPMENT.md](../DEVELOPMENT.md) - Guía de desarrollo
- [ ] [CONTRIBUTING.md](../CONTRIBUTING.md) - Guías de contribución
- [ ] [Architecture Overview](architecture.md) - Arquitectura del sistema
- [ ] ADRs relevantes en `/docs`

**5. Primera Ejecución Local (1 hora)**
- [ ] `make local-up` - Iniciar infraestructura local
- [ ] `make local-bootstrap` - Crear recursos
- [ ] Explorar las APIs en http://localhost:8000/docs
- [ ] Hacer un request de prueba

**6. Q&A con Buddy (30 min)**
- Reunión con el "buddy" asignado
- Responder dudas del día
- Planificar el día 2

### Día 2: Profundización Técnica

#### Mañana (9:00 AM - 12:00 PM)

**1. Daily Standup (15 min)**
- Primera participación en el daily
- Presentación breve al equipo

**2. Code Walkthrough (2 horas)**
- Sesión con Senior Developer
- Revisar estructura de código
- Entender patrones y convenciones
- Explorar cada microservicio:
  - `policy-svc` - Gestión de pólizas
  - `claim-svc` - Gestión de reclamaciones
  - `search-svc` - Búsqueda con OpenSearch
  - `ingest-svc` - Procesamiento de eventos
  - `gateway-bff` - API Gateway

**3. Arquitectura de Eventos (45 min)**
- Entender event-driven architecture
- Revisar contratos de eventos en `/contracts`
- Ver flujo: SNS → SQS → Lambda → S3/DynamoDB

#### Tarde (2:00 PM - 5:00 PM)

**4. Debugging y Troubleshooting (1 hora)**
- Cómo leer logs de Lambda
- Usar CloudWatch
- Debugging local con VS Code
- Herramientas útiles

**5. Primera Tarea - Bug Fix Sencillo (2 horas)**
- Tomar un ticket "good first issue"
- Crear rama feature
- Hacer el fix
- Escribir tests
- Crear draft PR

### Día 3: Contribución Activa

#### Mañana (9:00 AM - 12:00 PM)

**1. Code Review de tu PR (1 hora)**
- Recibir feedback del equipo
- Hacer ajustes necesarios
- Entender el proceso de review

**2. Testing Deep Dive (2 horas)**
- Estrategia de testing del proyecto
- Escribir unit tests
- Escribir integration tests
- Mocking y fixtures
- Ejecutar `make test-coverage`

#### Tarde (2:00 PM - 5:00 PM)

**3. CI/CD Pipeline (1 hora)**
- Entender GitHub Actions
- Ver deployment process
- Revisar jobs de CI
- Entender environments (dev/staging/prod)

**4. Segunda Tarea - Feature Pequeña (2 horas)**
- Tomar un ticket de feature pequeña
- Implementar con tests
- Documentar cambios
- Crear PR completo

### Día 4: Infraestructura y AWS

#### Mañana (9:00 AM - 12:00 PM)

**1. Terraform Overview (1.5 horas)**
- Estructura de `/infra`
- Módulos de Terraform
- Cómo hacer cambios de infraestructura
- `make tf-plan` y `make tf-apply`

**2. AWS Services Tour (1.5 horas)**
- DynamoDB - Database per service
- S3 - Data lake (bronze/silver)
- Lambda - Serverless compute
- SNS/SQS - Messaging
- OpenSearch/Elasticsearch - Search
- CloudWatch - Monitoring

#### Tarde (2:00 PM - 5:00 PM)

**3. Monitoreo y Observabilidad (1.5 horas)**
- CloudWatch dashboards
- Logs y métricas
- Alertas y alarmas
- X-Ray tracing

**4. Tercera Tarea - Feature Mediana (1.5 horas)**
- Comenzar feature más compleja
- Aplicar todo lo aprendido

### Día 5: Integration y Best Practices

#### Mañana (9:00 AM - 12:00 PM)

**1. Security Best Practices (1 hora)**
- IAM policies
- Secrets management
- Validación de inputs
- Authentication/Authorization

**2. Performance y Escalabilidad (1 hora)**
- Optimización de queries
- Caching strategies
- Lambda cold starts
- DynamoDB patterns

**3. Completar Feature (1 hora)**
- Finalizar tarea del día 4
- Tests completos
- Documentación

#### Tarde (2:00 PM - 5:00 PM)

**4. Retrospectiva de Onboarding (30 min)**
- Feedback sobre el proceso
- Áreas de mejora
- Dudas pendientes

**5. Pair Programming (1.5 horas)**
- Sesión con otro developer
- Trabajar en tarea conjunta
- Aprender técnicas del equipo

**6. Planning Next Week (1 hora)**
- Revisar sprint board
- Tomar tickets para próxima semana
- Planificar objetivos

## 📋 Checklist Completo de Onboarding

### Accesos y Permisos
- [ ] GitHub repository access
- [ ] AWS IAM user created (Developer role)
- [ ] Slack channels joined
- [ ] Jira/Linear access
- [ ] Confluence/Notion access
- [ ] Email distribution lists
- [ ] Calendar invites (Daily, Sprint Planning, Retro)

### Herramientas Instaladas
- [ ] Python 3.11+
- [ ] Docker Desktop
- [ ] AWS CLI v2
- [ ] Terraform 1.5+
- [ ] VS Code (con extensiones recomendadas)
- [ ] Git configurado
- [ ] Pre-commit hooks instalados

### Código y Ambiente
- [ ] Repositorio clonado
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Infraestructura local funcionando
- [ ] Tests pasando localmente
- [ ] Primera PR creada
- [ ] Primera PR mergeada

### Conocimiento del Proyecto
- [ ] Arquitectura entendida
- [ ] ADRs leídos
- [ ] Event contracts entendidos
- [ ] Testing strategy clara
- [ ] CI/CD pipeline entendido
- [ ] Deployment process conocido

### Integración al Equipo
- [ ] Buddy asignado
- [ ] Primera tarea completada
- [ ] Participación en daily
- [ ] Participación en planning
- [ ] Code review dado
- [ ] Code review recibido

## 🤝 Sistema de Buddies

Cada nuevo miembro tiene un "buddy" asignado por 30 días:

**Responsabilidades del Buddy:**
- Check-in diario (15 min)
- Responder preguntas
- Code reviews prioritarias
- Introducir al equipo
- Mentoring técnico

**Parejas de Buddy Sugeridas:**
- Backend focus → Senior Backend Developer
- Frontend focus → Senior Frontend Developer
- DevOps focus → DevOps Lead
- Full-stack → Tech Lead

## 📚 Recursos de Aprendizaje

### Internos
- [Architecture Decision Records](../docs/)
- [API Documentation](http://localhost:8000/docs) (local)
- [Runbooks](../docs/runbooks/)
- Team Wiki en Confluence

### Externos
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Event-Driven Architecture Patterns](https://microservices.io/patterns/data/event-driven-architecture.html)

## 🎯 Objetivos del Primer Mes

### Semana 1
- ✅ Ambiente configurado
- ✅ Primera PR mergeada
- ✅ Familiarizado con arquitectura

### Semana 2
- ✅ 3-5 PRs mergeadas
- ✅ Comfortable con el stack técnico
- ✅ Participación activa en code reviews

### Semana 3
- ✅ Feature mediana completada
- ✅ Contribución a documentación
- ✅ Mentoring de próximo nuevo miembro (opcional)

### Semana 4
- ✅ Autonomía en tareas
- ✅ Liderando alguna iniciativa pequeña
- ✅ Integrado completamente al equipo

## 💬 Canales de Comunicación

### Slack
- `#insurance-platform-dev` - Desarrollo y preguntas técnicas
- `#insurance-platform-alerts` - Alertas de producción
- `#insurance-platform-general` - Discusiones generales
- `#random` - Socialización

### Reuniones Recurrentes
- **Daily Standup**: Lun-Vie 9:00 AM (15 min)
- **Sprint Planning**: Cada 2 semanas, Lunes 10:00 AM (2 horas)
- **Sprint Review**: Cada 2 semanas, Viernes 2:00 PM (1 hora)
- **Retrospective**: Cada 2 semanas, Viernes 3:00 PM (1 hora)
- **Tech Talks**: Viernes alternos, 4:00 PM (30 min)

## 🆘 ¿Necesitas Ayuda?

1. **Pregunta a tu Buddy** - Primera línea de soporte
2. **Slack `#insurance-platform-dev`** - Preguntas técnicas
3. **Tech Lead** - Decisiones arquitectónicas
4. **DevOps Lead** - Infraestructura y deployments
5. **Product Owner** - Requerimientos de producto

## 📝 Feedback del Onboarding

Al final de tu primera semana, por favor llena el formulario de feedback:
- ¿Qué fue útil?
- ¿Qué podemos mejorar?
- ¿Qué faltó?
- ¿Recomendaciones?

Esto nos ayuda a mejorar el proceso para futuros miembros del equipo.

---

**¡Bienvenido al equipo! Estamos emocionados de trabajar contigo.** 🎉

Si tienes preguntas, no dudes en preguntar. Todos estamos aquí para ayudarte a tener éxito. 🚀

