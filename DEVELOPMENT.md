# Development Guide

Guía completa para desarrolladores que se unen al equipo.

## 📋 Tabla de Contenidos

- [Bienvenida](#bienvenida)
- [Requisitos Previos](#requisitos-previos)
- [Configuración Inicial](#configuración-inicial)
- [Acceso a AWS](#acceso-a-aws)
- [Desarrollo Local](#desarrollo-local)
- [Workflow Diario](#workflow-diario)
- [Herramientas y Comandos](#herramientas-y-comandos)
- [Troubleshooting](#troubleshooting)

## 🎉 Bienvenida

Bienvenido al equipo de **Insurance Microservices Platform**. Esta guía te ayudará a configurar tu entorno de desarrollo y comenzar a contribuir.

> **Nota:** Si eres nuevo en el proyecto, te recomendamos leer primero el README.md para entender la arquitectura general.

## 📦 Requisitos Previos

### Software Requerido

Instala las siguientes herramientas antes de comenzar:

```bash
# 1. Python 3.11 o superior
python --version  # Debe mostrar 3.11.x

# 2. Docker y Docker Compose
docker --version
docker-compose --version

# 3. AWS CLI v2
aws --version

# 4. Terraform
terraform --version

# 5. Git
git --version

# 6. Make
make --version
```

### Instalación en macOS

```bash
# Usando Homebrew
brew install python@3.11
brew install docker
brew install awscli
brew install terraform
brew install git
brew install make
```

### Instalación en Linux (Ubuntu/Debian)

```bash
# Python
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

## 🚀 Configuración Inicial

### 1. Clonar el Repositorio

```bash
# Clona el repositorio
git clone https://github.com/tu-empresa/insurance-microservices.git
cd insurance-microservices

# Configura tu información de git
git config user.name "Tu Nombre"
git config user.email "tu.email@empresa.com"
```

### 2. Configurar Credenciales AWS

**Solicita al administrador del equipo:**
- AWS Access Key ID
- AWS Secret Access Key
- Nombre del rol IAM asignado

```bash
# Configura AWS CLI
aws configure

# Ingresa cuando se solicite:
# AWS Access Key ID: [tu-access-key]
# AWS Secret Access Key: [tu-secret-key]
# Default region name: us-east-1
# Default output format: json

# Verifica la configuración
aws sts get-caller-identity
```

**Salida esperada:**
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "202235431150",
    "Arn": "arn:aws:iam::202235431150:user/tu-nombre"
}
```

### 3. Configurar Entorno Local

```bash
# Copia el archivo de configuración de ejemplo
cp env.example .env

# Edita .env con tus valores locales
vim .env  # o usa tu editor favorito
```

**Archivo `.env` básico:**
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=202235431150

# Local Development
ENV=local
LOG_LEVEL=DEBUG

# DynamoDB Local
DYNAMODB_ENDPOINT_URL=http://localhost:8000

# S3 Local (LocalStack)
S3_ENDPOINT_URL=http://localhost:4566

# OpenSearch Local
OPENSEARCH_ENDPOINT=localhost:9200
```

### 4. Instalar Dependencias Python

```bash
# Crea un entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instala dependencias para desarrollo
pip install --upgrade pip
pip install -r requirements-dev.txt

# Instala dependencias de cada servicio
cd services/policy-svc
pip install -r requirements.txt
cd ../..
```

### 5. Iniciar Infraestructura Local

```bash
# Inicia todos los servicios locales (DynamoDB, LocalStack, etc.)
make local-up

# Espera unos segundos para que los servicios inicien
sleep 10

# Verifica que todo esté corriendo
make local-status
```

**Servicios locales disponibles:**
- DynamoDB Local: http://localhost:8000
- LocalStack (S3): http://localhost:4566
- OpenSearch: http://localhost:9200

### 6. Crear Recursos Locales

```bash
# Crea tablas DynamoDB, buckets S3, etc.
make local-bootstrap

# Carga datos de prueba (opcional)
make local-seed
```

### 7. Ejecutar Tests

```bash
# Ejecuta todos los tests
make test

# Ejecuta tests con cobertura
make test-coverage

# Abre el reporte de cobertura
open htmlcov/index.html  # En Linux: xdg-open htmlcov/index.html
```

## 🏢 Acceso a AWS

### Ambientes Disponibles

- **dev**: Desarrollo compartido en AWS
- **staging**: Pre-producción
- **production**: Producción (acceso restringido)

### Permisos por Rol

#### Developer Role
- ✅ Leer recursos en dev/staging
- ✅ Ver logs de Lambda
- ✅ Ver métricas de CloudWatch
- ❌ No puede crear/modificar infraestructura
- ❌ No puede acceder a producción

#### DevOps Role
- ✅ Todo lo de Developer
- ✅ Crear/modificar recursos en dev/staging
- ✅ Ejecutar Terraform
- ✅ Ver secretos (con justificación)
- ⚠️ Acceso limitado a producción

#### Admin Role
- ✅ Acceso completo a todos los ambientes
- ✅ Gestión de usuarios y permisos
- ✅ Acceso a producción

### Solicitar Acceso

1. Crea un ticket en Jira/ServiceNow
2. Especifica el rol y ambientes necesarios
3. Justifica el acceso
4. Espera aprobación del team lead
5. Recibirás credenciales por correo seguro

## 💻 Desarrollo Local

### Estructura del Proyecto

```
insurance-microservices/
├── services/              # Microservicios
│   ├── policy-svc/       # Gestión de pólizas
│   ├── claim-svc/        # Gestión de reclamaciones
│   ├── gateway-bff/      # API Gateway
│   ├── search-svc/       # Búsqueda con OpenSearch
│   └── ingest-svc/       # Procesamiento de eventos
├── shared/               # Código compartido
├── infra/                # Infraestructura como código
│   └── terraform/
├── tests/                # Tests de integración
├── docs/                 # Documentación
├── contracts/            # Contratos de eventos
└── local/                # Configuración local
```

### Ejecutar un Servicio Localmente

```bash
# Navega al servicio
cd services/policy-svc

# Activa el entorno virtual
source ../../venv/bin/activate

# Ejecuta el servicio
uvicorn app.main:app --reload --port 8001

# El servicio estará disponible en:
# http://localhost:8001
# Documentación: http://localhost:8001/docs
```

### Ejecutar Todos los Servicios

```bash
# Desde la raíz del proyecto
make services-up

# Los servicios estarán disponibles en:
# - Gateway BFF: http://localhost:8000
# - Policy Service: http://localhost:8001
# - Claim Service: http://localhost:8002
# - Search Service: http://localhost:8003
```

### Hot Reload

Todos los servicios usan `--reload` en desarrollo, por lo que los cambios se reflejan automáticamente.

## 📝 Workflow Diario

### 1. Sincronizar con Main

```bash
# Cada mañana, sincroniza tu código
git checkout main
git pull origin main

# Si estás en una rama feature
git checkout feature/mi-feature
git rebase main  # o git merge main
```

### 2. Crear una Nueva Feature

```bash
# Crea una rama desde main actualizado
git checkout main
git pull origin main
git checkout -b feature/agregar-validacion-premium

# Realiza tus cambios
# ... edita archivos ...

# Verifica que todo funcione
make test
make lint
make typecheck
```

### 3. Commit y Push

```bash
# Agrega cambios
git add .

# Commit con mensaje convencional
git commit -m "feat(policy-svc): add premium validation logic"

# Push a tu rama
git push origin feature/agregar-validacion-premium
```

### 4. Crear Pull Request

1. Ve a GitHub
2. Click en "Compare & pull request"
3. Llena la plantilla del PR
4. Asigna revisores (mínimo 1)
5. Agrega labels apropiados
6. Espera revisión y aprobación

### 5. Después del Merge

```bash
# Vuelve a main
git checkout main
git pull origin main

# Elimina tu rama local
git branch -d feature/agregar-validacion-premium

# Elimina la rama remota
git push origin --delete feature/agregar-validacion-premium
```

## 🛠️ Herramientas y Comandos

### Makefile Commands

```bash
# Desarrollo local
make local-up              # Inicia infraestructura local
make local-down            # Detiene infraestructura local
make local-bootstrap       # Crea recursos locales
make local-seed            # Carga datos de prueba
make local-status          # Muestra estado de servicios

# Servicios
make services-up           # Inicia todos los microservicios
make services-down         # Detiene todos los microservicios
make service-policy        # Inicia solo policy-svc
make service-claim         # Inicia solo claim-svc

# Testing
make test                  # Ejecuta todos los tests
make test-unit             # Solo tests unitarios
make test-integration      # Solo tests de integración
make test-coverage         # Tests con reporte de cobertura

# Calidad de código
make lint                  # Ejecuta linter (ruff)
make format               # Formatea código
make typecheck            # Verifica tipos (mypy)
make check                # Ejecuta todas las verificaciones

# Docker
make docker-build          # Construye imágenes Docker
make docker-push           # Sube imágenes a ECR

# Infraestructura
make tf-plan              # Plan de Terraform
make tf-apply             # Aplica cambios de Terraform
make tf-destroy           # Destruye infraestructura

# Utilidades
make clean                # Limpia archivos temporales
make help                 # Muestra ayuda
```

### VS Code Setup

Instala las extensiones recomendadas:

```bash
# Crea archivo de configuración
cat > .vscode/extensions.json << 'EOF'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform",
    "github.copilot",
    "eamodio.gitlens"
  ]
}
EOF
```

**Settings recomendados** (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Pre-commit Hooks

```bash
# Instala pre-commit
pip install pre-commit

# Instala los hooks
pre-commit install

# Ejecuta manualmente en todos los archivos
pre-commit run --all-files
```

## 🐛 Troubleshooting

### Docker Issues

**Problema**: "Cannot connect to Docker daemon"
```bash
# Solución: Inicia Docker Desktop
# macOS: Abre Docker Desktop desde Applications
# Linux: 
sudo systemctl start docker
```

**Problema**: "Port already in use"
```bash
# Encuentra el proceso usando el puerto
lsof -i :8000

# Mata el proceso
kill -9 <PID>

# O usa un puerto diferente
uvicorn app.main:app --reload --port 8099
```

### AWS Issues

**Problema**: "UnauthorizedOperation" al ejecutar comandos AWS
```bash
# Verifica tus credenciales
aws sts get-caller-identity

# Verifica permisos con tu team lead
# Puede que necesites un rol diferente
```

**Problema**: "Invalid credentials"
```bash
# Reconfigura AWS CLI
aws configure

# O usa variables de entorno
export AWS_ACCESS_KEY_ID="tu-access-key"
export AWS_SECRET_ACCESS_KEY="tu-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Python Issues

**Problema**: "Module not found"
```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

**Problema**: "Wrong Python version"
```bash
# Verifica versión
python --version

# Usa pyenv para gestionar versiones
brew install pyenv
pyenv install 3.11.5
pyenv local 3.11.5
```

### Tests Failing

**Problema**: Tests fallan localmente pero pasan en CI
```bash
# Limpia caché de pytest
pytest --cache-clear

# Limpia archivos __pycache__
find . -type d -name __pycache__ -exec rm -r {} +

# Reinstala dependencias
pip install -r requirements.txt --force-reinstall
```

## 📞 Obtener Ayuda

### Canales de Comunicación

- **Slack**: `#insurance-platform-dev` - Preguntas generales
- **Slack**: `#insurance-platform-alerts` - Alertas de producción
- **Jira**: Para reportar bugs y solicitar features
- **Confluence**: Documentación adicional y guías

### Contactos Clave

- **Tech Lead**: @nombre - Decisiones técnicas
- **DevOps Lead**: @nombre - Infraestructura y CI/CD
- **Product Owner**: @nombre - Requerimientos de producto
- **Scrum Master**: @nombre - Proceso y metodología

### Recursos Adicionales

- [Documentación de AWS](https://docs.aws.amazon.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Terraform Docs](https://www.terraform.io/docs)
- [Internal Wiki](https://wiki.empresa.com/insurance-platform)

## 🎯 Próximos Pasos

Ahora que tienes todo configurado:

1. ✅ Lee el [CONTRIBUTING.md](CONTRIBUTING.md)
2. ✅ Revisa los [ADRs](docs/) para entender decisiones arquitectónicas
3. ✅ Familiarízate con el código explorando los servicios
4. ✅ Toma un ticket de "good first issue" en Jira
5. ✅ Únete al daily standup (9:00 AM en Slack)
6. ✅ Presenta tu primera PR! 🎉

---

**¡Bienvenido al equipo!** Si tienes preguntas, no dudes en preguntar en Slack. Todos estamos aquí para ayudar. 🚀

