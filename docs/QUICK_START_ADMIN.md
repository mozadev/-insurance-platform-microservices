# ⚡ Quick Start - Agregar Nuevo Developer (5 minutos)

Guía rápida para agregar un nuevo desarrollador al proyecto.

## 🎯 Proceso Completo

```
┌──────────────────────────────────────────────────────────┐
│  PASO 1: GitHub (2 min)                                  │
│  ✓ Agregar a repositorio                                 │
│  ✓ Asignar a team                                        │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  PASO 2: AWS (2 min)                                     │
│  ✓ Crear usuario IAM                                     │
│  ✓ Generar access keys                                   │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│  PASO 3: Comunicación (1 min)                            │
│  ✓ Enviar email de bienvenida                            │
│  ✓ Agregar a Slack                                       │
└──────────────────────────────────────────────────────────┘
                        ↓
                  ✅ ¡Listo!
```

---

## 1️⃣ GitHub (2 minutos)

### Opción A: Repositorio Personal

```bash
1. Ve a: https://github.com/tu-usuario/insurance-microservices
2. Click: Settings → Collaborators
3. Click: "Add people"
4. Busca: username del developer
5. Selecciona: "Write" access
6. Click: "Add [username] to this repository"
```

### Opción B: Organización (Recomendado)

```bash
1. Ve a: https://github.com/orgs/TU-ORG/teams/insurance-platform-developers
2. Click: "Members" → "Add a member"
3. Busca: username del developer
4. Click: "Add [username] to team"

✅ El developer automáticamente tendrá acceso al repositorio
```

**📧 GitHub enviará automáticamente un email de invitación**

---

## 2️⃣ AWS (2 minutos)

### Crear Usuario IAM

```bash
# 1. Crear usuario
aws iam create-user --user-name juan.perez

# 2. Agregar a grupo de developers
aws iam add-user-to-group \
  --user-name juan.perez \
  --group-name insurance-platform-developers

# 3. Crear access key
aws iam create-access-key --user-name juan.perez
```

**Resultado:**
```json
{
    "AccessKey": {
        "UserName": "juan.perez",
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Status": "Active",
        "CreateDate": "2025-10-15T12:00:00Z"
    }
}
```

⚠️ **Guarda las credenciales de manera segura** - No las envíes por email sin encriptar

---

## 3️⃣ Enviar Credenciales (1 minuto)

### Email de Bienvenida

```
Para: juan.perez@empresa.com
Asunto: Acceso a Insurance Platform - Credenciales

Hola Juan,

¡Bienvenido al equipo! Aquí están tus accesos:

🐙 GitHub:
- Repositorio: https://github.com/tu-empresa/insurance-microservices
- Revisa tu email para aceptar la invitación

☁️ AWS:
- Access Key ID: [ver archivo adjunto seguro]
- Secret Access Key: [ver archivo adjunto seguro]
- Región: us-east-1

📚 Primeros pasos:
1. Acepta la invitación de GitHub
2. Sigue la guía: DEVELOPMENT.md
3. Tu buddy @maria-garcia te contactará hoy

¿Preguntas? Escríbeme en Slack: @tech-lead

Saludos,
[Tu Nombre]
```

### Herramientas para Enviar Credenciales de Manera Segura

1. **1Password** - Compartir vault
2. **AWS Secrets Manager** - Compartir secreto
3. **Bitwarden** - Compartir colección
4. **GPG Email** - Email encriptado

---

## ✅ Checklist de Verificación

Asegúrate de que el developer pueda:

```bash
# En su máquina local:

# 1. Clonar el repositorio
git clone https://github.com/tu-empresa/insurance-microservices.git
✅ Funciona

# 2. Configurar AWS
aws configure
# Ingresa Access Key ID
# Ingresa Secret Access Key
# Región: us-east-1

aws sts get-caller-identity
✅ Debe mostrar su usuario

# 3. Verificar acceso a logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/ins-dev
✅ Debe ver los log groups

# 4. Ejecutar setup local
cd insurance-microservices
make setup
make test
✅ Tests pasan
```

---

## 🚀 Primeros Pasos del Developer

El developer debe:

1. **Aceptar invitación de GitHub** (revisa email)
2. **Clonar repo**: `git clone https://github.com/tu-empresa/insurance-microservices.git`
3. **Leer docs**:
   - `README.md` (10 min)
   - `DEVELOPMENT.md` (30 min)
4. **Setup**: `make setup && make local-up && make test`
5. **Contactar buddy** para sesión de onboarding

---

## 📊 Estadísticas Típicas

- **Tiempo de setup**: 2-3 horas
- **Primera PR**: Día 3
- **Productivo**: Semana 1
- **Autónomo**: Semana 4

---

## 🆘 Troubleshooting Rápido

### "No puedo clonar el repo"
```bash
# Verificar que aceptó la invitación de GitHub
# Verificar que tiene permisos "Write" o superior
# Intentar con HTTPS en vez de SSH (o viceversa)
```

### "AWS access denied"
```bash
# Verificar que está en el grupo correcto
aws iam list-groups-for-user --user-name juan.perez

# Verificar que configuró las credenciales correctamente
aws configure list
```

### "Tests fallan localmente"
```bash
# Verificar que Docker está corriendo
docker ps

# Verificar que la infraestructura local está up
make local-up
make local-status
```

---

## 📞 Contacto

¿Problemas? Contacta a:
- **Tech Lead**: @tech-lead (Slack)
- **DevOps**: @devops-lead (Slack)
- **HR**: hr@empresa.com

---

## 🔗 Links Útiles

- [Guía Completa de Admin](ADMIN_GUIDE.md)
- [Guía de Onboarding](ONBOARDING.md)
- [Guía de Desarrollo](../DEVELOPMENT.md)
- [Cómo Contribuir](../CONTRIBUTING.md)

---

**Tiempo total: ~5 minutos** ⏱️

**¡Nuevo developer productivo en < 1 día!** 🎉

