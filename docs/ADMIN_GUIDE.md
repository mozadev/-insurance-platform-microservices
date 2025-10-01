# 👨‍💼 Admin Guide - Gestión de Equipo y Accesos

Guía para Tech Leads, Managers y Administradores sobre cómo agregar y gestionar desarrolladores en el proyecto.

## 📋 Tabla de Contenidos

- [Agregar Nuevo Desarrollador](#agregar-nuevo-desarrollador)
- [Configurar Accesos GitHub](#configurar-accesos-github)
- [Configurar Accesos AWS](#configurar-accesos-aws)
- [Configurar GitHub Secrets](#configurar-github-secrets)
- [Gestión de Equipos](#gestión-de-equipos)
- [Permisos y Roles](#permisos-y-roles)
- [Offboarding](#offboarding)

---

## 🆕 Agregar Nuevo Desarrollador

### Checklist Completo

```
□ 1. Agregar a GitHub Organization/Repository
□ 2. Crear usuario IAM en AWS
□ 3. Agregar a Slack channels
□ 4. Agregar a Jira/Linear
□ 5. Agregar a calendar events
□ 6. Asignar buddy
□ 7. Enviar email de bienvenida
```

---

## 🔐 Configurar Accesos GitHub

### Opción 1: Repositorio Público (Open Source)

Si tu repo es público, cualquiera puede hacer fork y contribuir. Solo necesitas:

**Para contribuidores externos:**
- No necesitan ser agregados al repo
- Hacen fork del repositorio
- Crean PRs desde su fork
- Los maintainers revisan y aprueban

**Para maintainers del equipo:**
- Deben ser agregados al repo con permisos "Write" o "Maintain"

### Opción 2: Repositorio Privado (Empresas)

#### **Paso 1: Agregar al Repositorio**

**Si es un repositorio personal:**

1. Ve a tu repositorio en GitHub
2. Click en **"Settings"** → **"Collaborators"**
3. Click en **"Add people"**
4. Busca por username, nombre completo o email
5. Selecciona el nivel de acceso:
   - **Read**: Solo lectura (para QA, PO)
   - **Write**: Puede hacer push y crear PRs (developers)
   - **Maintain**: Write + gestión de settings (senior devs)
   - **Admin**: Control total (tech lead)

```bash
# Ejemplo visual:
GitHub.com → Repository → Settings → Collaborators → Add people
```

**Si es una Organización de GitHub:**

1. Ve a https://github.com/orgs/TU-ORGANIZACION/people
2. Click en **"Invite member"**
3. Ingresa el username o email del developer
4. Asigna a un equipo (Team) específico

#### **Paso 2: Crear Teams (Recomendado para organizaciones)**

Los teams facilitan la gestión de permisos:

**1. Ir a GitHub Organization**
```
https://github.com/orgs/TU-ORGANIZACION/teams
```

**2. Crear Teams**
```
📁 insurance-platform (Parent team)
  ├── 👥 insurance-platform-admins (Admin access)
  ├── 👥 insurance-platform-senior (Write + review)
  ├── 👥 insurance-platform-developers (Write)
  └── 👥 insurance-platform-readonly (Read)
```

**3. Asignar Permisos por Team**
- Ve a: Repository → Settings → Collaborators and teams
- Click "Add teams"
- Selecciona el team y el nivel de acceso

**4. Agregar Developer a Team**
```
Organization → Teams → [Seleccionar Team] → Members → Add member
```

#### **Paso 3: Configurar Branch Protection**

Protege la rama `main` para evitar cambios directos:

1. Ve a: **Settings** → **Branches** → **Add branch protection rule**

2. Configuración recomendada:
```
Branch name pattern: main

☑ Require a pull request before merging
  ☑ Require approvals: 1 (o 2 para producción)
  ☑ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require review from Code Owners (si usas CODEOWNERS)

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  Status checks:
    - ☑ test
    - ☑ lint
    - ☑ build

☑ Require conversation resolution before merging

☑ Require signed commits (opcional, más seguro)

☑ Include administrators (aplica reglas a admins también)
```

3. Click **"Create"**

#### **Paso 4: Configurar CODEOWNERS (Opcional pero recomendado)**

Asigna automáticamente reviewers según archivos modificados:

```bash
# Crear archivo .github/CODEOWNERS
cat > .github/CODEOWNERS << 'EOF'
# CODEOWNERS - Auto-assign reviewers

# Default owners for everything
* @tech-lead-username

# Infrastructure changes require DevOps approval
/infra/ @devops-lead-username @tech-lead-username
*.tf @devops-lead-username
*.tfvars @devops-lead-username

# GitHub Actions require admin approval
/.github/workflows/ @tech-lead-username

# Service owners
/services/policy-svc/ @policy-team-lead-username
/services/claim-svc/ @claim-team-lead-username
/services/search-svc/ @search-team-lead-username

# Shared code requires senior review
/shared/ @senior-dev-1 @senior-dev-2

# Documentation can be reviewed by anyone
/docs/ @tech-lead-username
*.md @tech-lead-username

# Security-sensitive files
/secrets/ @tech-lead-username @security-lead-username
*secret* @tech-lead-username @security-lead-username
EOF
```

---

## ☁️ Configurar Accesos AWS

### **Roles Recomendados**

#### **1. Developer Role** (Desarrolladores regulares)

```bash
# Crear usuario IAM
aws iam create-user --user-name developer-nombre

# Agregar a grupo de developers
aws iam add-user-to-group \
  --user-name developer-nombre \
  --group-name insurance-platform-developers

# Crear access key
aws iam create-access-key --user-name developer-nombre
```

**Permisos del Developer Role:**
- ✅ Ver logs de CloudWatch
- ✅ Ver métricas
- ✅ Describir recursos (read-only)
- ✅ Ejecutar queries en DynamoDB (dev environment)
- ❌ No puede modificar infraestructura
- ❌ No puede acceder a producción

**Política IAM para Developers:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "s3:GetObject",
        "s3:ListBucket",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListFunctions"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        },
        "StringLike": {
          "aws:ResourceTag/Environment": "dev"
        }
      }
    }
  ]
}
```

#### **2. DevOps Role** (Senior Developers / DevOps)

**Permisos adicionales:**
- ✅ Todo lo de Developer
- ✅ Modificar recursos en dev/staging
- ✅ Ejecutar Terraform apply
- ✅ Acceso a secretos (con logging)
- ⚠️ Acceso limitado a producción

#### **3. Admin Role** (Tech Lead / Architects)

**Permisos:**
- ✅ Control total en dev/staging
- ✅ Acceso completo a producción
- ✅ Gestión de IAM users
- ✅ Billing y costos

### **Crear Usuario IAM - Paso a Paso**

```bash
# 1. Crear el usuario
aws iam create-user --user-name juan.perez

# 2. Agregar al grupo (asume que el grupo ya existe)
aws iam add-user-to-group \
  --user-name juan.perez \
  --group-name insurance-platform-developers

# 3. Crear access key y guardar en lugar seguro
aws iam create-access-key --user-name juan.perez > juan-perez-credentials.json

# 4. (Opcional) Habilitar MFA para mayor seguridad
aws iam create-virtual-mfa-device \
  --virtual-mfa-device-name juan-perez-mfa \
  --outfile juan-perez-mfa-qr.png \
  --bootstrap-method QRCodePNG

# 5. Enviar credenciales de manera segura (email encriptado, 1Password, etc.)
```

### **Crear Grupos IAM (Una sola vez)**

```bash
# Crear grupos
aws iam create-group --group-name insurance-platform-admins
aws iam create-group --group-name insurance-platform-devops
aws iam create-group --group-name insurance-platform-developers

# Attach políticas (necesitas crear las políticas primero)
aws iam attach-group-policy \
  --group-name insurance-platform-developers \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/DeveloperPolicy

aws iam attach-group-policy \
  --group-name insurance-platform-devops \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/DevOpsPolicy

aws iam attach-group-policy \
  --group-name insurance-platform-admins \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

---

## 🔑 Configurar GitHub Secrets

Algunos developers (DevOps/Senior) pueden necesitar acceso para configurar secrets:

### **Secrets Necesarios**

```bash
# Para CI/CD (GitHub Actions)
OPENSEARCH_MASTER_PASSWORD    # Password de OpenSearch/Elasticsearch
AWS_ACCOUNT_ID                # ID de cuenta AWS
AWS_REGION                    # Región (us-east-1)
ECR_REPOSITORY                # Nombre del repo ECR
```

### **Agregar Secrets**

1. Ve a: **Repository** → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Nombre: `OPENSEARCH_MASTER_PASSWORD`
4. Valor: `tu-password-super-seguro`
5. Click **"Add secret"**

### **Secrets por Ambiente**

Para múltiples ambientes (dev/staging/prod):

1. Ve a: **Settings** → **Environments**
2. Click **"New environment"**: `dev`, `staging`, `production`
3. Agrega secrets específicos por ambiente
4. Configura protection rules (ej: producción requiere aprobación)

---

## 👥 Gestión de Equipos

### **Estructura Recomendada**

```
insurance-platform/
├── Team: Platform Admins
│   ├── Tech Lead
│   └── DevOps Lead
│   └── Access: Admin
│
├── Team: Senior Developers
│   ├── Senior Backend Dev
│   ├── Senior Frontend Dev
│   └── Access: Maintain + Require reviews
│
├── Team: Backend Developers
│   ├── Dev 1
│   ├── Dev 2
│   └── Access: Write
│
├── Team: Frontend Developers
│   ├── Dev 3
│   └── Access: Write
│
└── Team: QA & Product
    ├── QA Lead
    ├── Product Owner
    └── Access: Read + Can create issues
```

### **Asignar Buddy**

Para cada nuevo developer, asigna un buddy:

```markdown
# En GitHub Issue o Notion:
👤 **Nuevo Developer**: Juan Pérez (@jperez)
🤝 **Buddy Asignado**: María García (@mgarcia)
📅 **Fecha inicio**: 2025-10-15
📋 **Checklist**: docs/ONBOARDING.md
```

---

## 🔒 Permisos y Roles

### **Matriz de Permisos**

| Acción                        | Junior Dev | Mid Dev | Senior Dev | DevOps | Admin |
|-------------------------------|-----------|---------|------------|--------|-------|
| Clonar repositorio            | ✅        | ✅      | ✅         | ✅     | ✅    |
| Crear branch                  | ✅        | ✅      | ✅         | ✅     | ✅    |
| Crear PR                      | ✅        | ✅      | ✅         | ✅     | ✅    |
| Aprobar PR                    | ❌        | ✅      | ✅         | ✅     | ✅    |
| Merge a main                  | ❌        | ⚠️      | ✅         | ✅     | ✅    |
| Push directo a main           | ❌        | ❌      | ❌         | ❌     | ✅    |
| Modificar GitHub Actions      | ❌        | ❌      | ⚠️         | ✅     | ✅    |
| Ver logs AWS (dev)            | ✅        | ✅      | ✅         | ✅     | ✅    |
| Ver logs AWS (prod)           | ❌        | ❌      | ⚠️         | ✅     | ✅    |
| Terraform apply (dev)         | ❌        | ❌      | ⚠️         | ✅     | ✅    |
| Terraform apply (prod)        | ❌        | ❌      | ❌         | ⚠️     | ✅    |
| Gestionar secretos            | ❌        | ❌      | ❌         | ✅     | ✅    |
| Agregar usuarios              | ❌        | ❌      | ❌         | ❌     | ✅    |

---

## 📧 Email de Bienvenida (Template)

```
Asunto: ¡Bienvenido al equipo de Insurance Platform! 🎉

Hola [Nombre],

¡Bienvenido al equipo! Estamos emocionados de tenerte con nosotros.

📋 **Tu información de acceso:**

**GitHub:**
- Username: Tu usuario de GitHub
- Repositorio: https://github.com/tu-empresa/insurance-microservices
- Ya tienes acceso con permisos de "Write"

**AWS:**
- Access Key ID: [Enviado por separado de manera segura]
- Secret Access Key: [Enviado por separado de manera segura]
- Región: us-east-1
- Rol: Developer

**Slack:**
- Ya fuiste agregado a:
  - #insurance-platform-dev
  - #insurance-platform-general
  - #insurance-platform-alerts

**Jira:**
- URL: https://tu-empresa.atlassian.net
- Ya tienes acceso al proyecto "INSURANCE"

🤝 **Tu Buddy:**
- Nombre: [Nombre del Buddy]
- Slack: @buddy-username
- Tendrán un check-in diario durante tu primera semana

📚 **Primeros pasos:**

1. Clona el repositorio:
   ```
   git clone https://github.com/tu-empresa/insurance-microservices.git
   ```

2. Lee la documentación:
   - README.md - Overview
   - DEVELOPMENT.md - Setup detallado
   - ONBOARDING.md - Plan de primera semana

3. Configura tu ambiente:
   ```
   make setup
   make local-up
   make test
   ```

4. Tu buddy te contactará hoy para una sesión de onboarding

📅 **Reuniones:**
- Daily Standup: Lun-Vie 9:00 AM
- Tu buddy te agregará al calendar

Si tienes preguntas, no dudes en preguntar en Slack o directamente a tu buddy.

¡Bienvenido al equipo! 🚀

Saludos,
[Tech Lead Name]
```

---

## 🚪 Offboarding

Cuando un developer deja el equipo:

### **Checklist de Offboarding**

```
□ 1. Remover de GitHub repository/organization
□ 2. Deshabilitar usuario IAM en AWS
□ 3. Revocar access keys
□ 4. Remover de Slack
□ 5. Remover de Jira/Linear
□ 6. Remover de calendar events
□ 7. Reasignar tickets/PRs pendientes
□ 8. Hacer knowledge transfer
```

### **Comandos AWS**

```bash
# 1. Listar access keys del usuario
aws iam list-access-keys --user-name developer-nombre

# 2. Deshabilitar access keys
aws iam update-access-key \
  --user-name developer-nombre \
  --access-key-id AKIAXXXXXXXXXXXXXXXX \
  --status Inactive

# 3. Eliminar access keys
aws iam delete-access-key \
  --user-name developer-nombre \
  --access-key-id AKIAXXXXXXXXXXXXXXXX

# 4. Remover de grupos
aws iam remove-user-from-group \
  --user-name developer-nombre \
  --group-name insurance-platform-developers

# 5. Eliminar usuario (después de remover de todos los grupos)
aws iam delete-user --user-name developer-nombre
```

### **GitHub**

1. Ve a: **Repository** → **Settings** → **Collaborators**
2. Encuentra al usuario
3. Click **"Remove"**

O para organizaciones:
1. Ve a: **Organization** → **People**
2. Encuentra al usuario
3. Click **"..."** → **"Remove from organization"**

---

## 📊 Dashboard de Administración

### **Métricas a Monitorear**

- **Team Size**: Número de developers activos
- **Onboarding Success**: Tiempo hasta primera PR
- **PR Velocity**: PRs creados/mergeados por semana
- **Code Review Time**: Tiempo promedio de review
- **Bug Rate**: Bugs por sprint
- **Test Coverage**: % de cobertura de tests
- **Deploy Frequency**: Deploys por semana

### **Herramientas Recomendadas**

- **GitHub Insights**: Estadísticas del repositorio
- **AWS Cost Explorer**: Monitoreo de costos
- **CloudWatch Dashboards**: Métricas de aplicación
- **Jira/Linear**: Tracking de tickets

---

## 🆘 Troubleshooting Común

### **"Developer no puede hacer push"**
- Verificar permisos en GitHub
- Verificar branch protection rules
- Verificar que no esté intentando push directo a main

### **"Developer no puede ver logs de AWS"**
- Verificar que tiene IAM user
- Verificar que está en el grupo correcto
- Verificar que configuró AWS CLI correctamente

### **"CI/CD falla por permisos"**
- Verificar GitHub secrets configurados
- Verificar IAM role para GitHub Actions (OIDC)
- Ver logs de GitHub Actions

---

**Contacto para Administración:**
- Tech Lead: @tech-lead-username
- DevOps Lead: @devops-lead-username
- HR/People Ops: hr@tu-empresa.com

