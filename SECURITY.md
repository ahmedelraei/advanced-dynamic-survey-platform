# ADSP Security & Compliance Documentation

## Role-Based Access Control (RBAC)

### Overview
The system implements three-tier RBAC using Django's built-in Groups and Permissions, extended with django-guardian for object-level permissions.

### Roles & Permissions

#### 1. **Survey Admins** (`survey_admins`)
**Full Access** - Complete control over surveys and data

**Permissions:**
- ✅ Create, Read, Update, Delete surveys
- ✅ Create, Read, Update, Delete sections/fields
- ✅ View all responses
- ✅ Export data
- ✅ Manage user permissions
- ✅ Access audit logs

**Use Case:** Platform administrators, survey managers

---

#### 2. **Survey Analysts** (`survey_analysts`)
**Read + Limited Write** - Can create and modify but not delete

**Permissions:**
- ✅ Create, Read, Update surveys (no delete)
- ✅ Create, Read, Update sections/fields (no delete)
- ✅ View responses
- ✅ Export data
- ❌ Cannot delete surveys
- ❌ Cannot manage permissions

**Use Case:** Data analysts, researchers, survey designers

---

#### 3. **Survey Viewers** (`survey_viewers`)
**Read Only** - View-only access

**Permissions:**
- ✅ View surveys
- ✅ View sections/fields
- ✅ View responses
- ❌ Cannot create, update, or delete
- ❌ Cannot export data

**Use Case:** Stakeholders, report viewers

---

## Implementation Details

### Permission Classes

Located in `apps/users/permissions.py`:

```python
# Custom DRF permission classes
- IsSurveyAdmin
- IsSurveyAnalyst
- IsSurveyViewer
- IsSurveyOwner
- CanManageSurvey (composite)
```

### Object-Level Permissions

Using **django-guardian** for fine-grained control:
- Survey owners have full access to their surveys
- Permissions can be granted per-survey
- Supports team-based access control

---

## Audit Logging

### Overview
**Immutable audit trail** tracking all system actions for compliance.

### What's Logged

#### Automatic Logging (via Middleware)
All API mutations are automatically logged:
- POST, PUT, PATCH, DELETE requests
- User identity
- IP address
- Request path and method
- Timestamp
- Changes made (JSONB diff)

#### Manual Logging
Programmatic logging for specific events:
```python
from apps.audit.middleware import log_audit_event
from apps.audit.models import AuditAction

log_audit_event(
    action=AuditAction.CREATE,
    user=request.user,
    obj=survey,
    description="Survey created",
    request=request
)
```

### Audit Actions Tracked

- `CREATE` - Resource creation
- `READ` - Data access (for PII)
- `UPDATE` - Modifications
- `DELETE` - Deletions
- `LOGIN` / `LOGOUT` - Authentication
- `EXPORT` - Data exports
- `PII_ACCESS` - Sensitive data access

### Audit Log Model

**Location:** `apps/audit/models.py`

**Fields:**
- `id` - UUID
- `action` - Action type
- `user` - Actor (nullable for anonymous)
- `content_type` / `object_id` - Target object (generic relation)
- `changes` - JSONB field with before/after values
- `ip_address` - Client IP
- `user_agent` - Browser/client info
- `request_path` - API endpoint
- `timestamp` - When action occurred

**Immutability:**
- Cannot update existing logs
- Cannot delete logs
- Append-only design

---

## Setup Instructions

### 1. Create RBAC Groups

```bash
docker compose exec web python manage.py setup_rbac
```

This creates the three groups with appropriate permissions.

### 2. Assign Users to Groups

**Via Django Admin:**
1. Go to `/admin/auth/user/`
2. Edit user
3. Add to groups: `survey_admins`, `survey_analysts`, or `survey_viewers`

**Via Code:**
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
user = User.objects.get(username='analyst1')
analyst_group = Group.objects.get(name='survey_analysts')
user.groups.add(analyst_group)
```

### 3. View Audit Logs

**Django Admin:** `/admin/audit/auditlog/`

**Programmatically:**
```python
from apps.audit.models import AuditLog

# All actions by a user
logs = AuditLog.objects.filter(user=user)

# All actions on a survey
logs = AuditLog.objects.filter(
    content_type=ContentType.objects.get_for_model(Survey),
    object_id=survey_id
)

# PII access logs
pii_logs = AuditLog.objects.filter(action='pii_access')
```

---

## Security Best Practices

### 1. **Principle of Least Privilege**
- Assign minimal permissions needed
- Use `survey_viewers` by default
- Promote to `survey_analysts` only when needed

### 2. **Audit Review**
- Regularly review audit logs
- Monitor PII access
- Alert on suspicious patterns

### 3. **Session Security**
- Sessions expire after inactivity
- HTTPS required in production
- CSRF protection enabled

### 4. **Data Protection**
- Sensitive fields marked with `is_sensitive=True`
- PII stored in `encrypted_data` field
- IP addresses logged for accountability

---

## Compliance Features

✅ **GDPR Ready**
- Audit trail for data access
- PII encryption
- Right to deletion (soft delete)

✅ **SOC 2 Compatible**
- Immutable audit logs
- Role-based access control
- Change tracking

✅ **HIPAA Considerations**
- Encrypted sensitive data
- Access logging
- User authentication

---

## API Endpoints

### RBAC Management
- Handled via Django Admin
- Future: Add API endpoints for group management

### Audit Logs
- Read-only via Django Admin
- Future: Add API endpoint for audit log queries

---

## Testing RBAC

```bash
# Run permission tests
pytest apps/users/tests/test_permissions.py -v

# Test audit logging
pytest apps/audit/tests/test_audit.py -v
```
