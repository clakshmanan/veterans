# AI Agent Instructions - Veteran Association Management System

## System Overview
This is a Django 5.1.3 multi-tenant veteran management system with hierarchical user roles: superusers (admins), state admins (`state_{CODE}` usernames), and veterans. The system manages veteran records, family details, financial transactions, and social features across Indian states.

## Architecture & Data Flow

### User Authentication Pattern
- **Superusers**: Full system access, manage all states
- **State Admins**: Username pattern `state_{STATE_CODE}` (e.g., `state_AP` for Andhra Pradesh)
- **Veterans**: Linked to VeteranMember records, require approval by state admins
- Authentication middleware enforces state-based access control via `UserStateMiddleware`

### Core Models Hierarchy
```
State → VeteranMember ← User (via VeteranUser or UserState)
     ↓
   Child → JobPortal/Matrimonial
     ↓
   Transaction/Financial records
```

### Critical State-Based Access Control
The system enforces strict data isolation:
- `VeteranMember.clean()` validates that non-superusers can only create/edit members in their assigned state
- Views use `@validate_state_access` decorator for authorization
- URL patterns include `state_id` for context-aware routing

## Development Workflows

### Database Management
```bash
# Core data seeding (run in order)
python manage.py seed_data          # Master data (states, ranks, groups)
python manage.py seed_state_users   # Create state admin accounts
python manage.py seed_members       # Sample member data for testing

# Development server
python manage.py runserver
```

### File Upload System
- Documents use `get_upload_path()` function for organized storage by type and date
- Path pattern: `documents/{category}/{year}/{month}/filename`
- Categories: pdf, images, office, other
- Security: FileExtensionValidator with approved extensions only

### Form Validation Pattern
Forms exclude `state` field - it's set automatically in views based on user's state assignment:
```python
# In VeteranMemberForm - state is excluded from fields
# In views - state is set programmatically:
form.instance.state = user_state.state
form.instance.created_by = request.user
```

## Project-Specific Conventions

### Service Number vs P-Number
- Legacy: `p_number` (optional, kept for compatibility)  
- Current: `service_number` (unique, required) - format: `digits-hyphen-letter` (e.g., `12345-A`)
- Always use `service_number` for new implementations

### URL Routing Strategy
All member operations are state-scoped:
- `/state/<state_id>/members/` - List members
- `/state/<state_id>/add-member/` - Add member
- `/member/<member_id>/edit/` - Edit (validates state access)

### Security Middleware Stack
1. `SecurityHeadersMiddleware` - Adds security headers
2. `RequestValidationMiddleware` - Blocks suspicious patterns
3. `SessionSecurityMiddleware` - IP-based session validation
4. `UserStateMiddleware` - Tracks user activity

### Financial System
- `FinancialYear` model drives all financial operations
- `Transaction` model handles subscriptions, donations, expenses
- Auto-calculated subscription due dates (365 days from payment)
- Status tracking: Active/Due Soon/Overdue with 15-day grace period

## Integration Points

### File Handling
- Profile photos → `profiles/%Y/%m/`
- Documents → `documents/{type}/%Y/%m/`
- Children photos → `children/%Y/%m/`
- Resumes → `resumes/%Y/%m/`

### Relationship Dependencies
When working with veterans:
1. Check `VeteranUser` relationship for user accounts
2. Access children via `veteran.children.all()`
3. Financial records via `veteran.transactions.all()`
4. Chat features require cross-state veteran lookup

### Template Context Patterns
Views consistently provide:
- `user_state` - Current user's state assignment
- `is_state_admin` - Boolean for UI conditional rendering  
- `subscription_status` - Veteran payment status with color coding
- Form error handling with detailed validation messages

## Common Pitfalls

### Form Submission Issues
- Never include `state` in form fields - set in view logic
- Always call `form.instance.created_by = request.user` before save
- Use `full_clean()` to trigger model validation

### State Access Violations  
- Check user permissions before state operations
- Use `get_object_or_404` with state filtering for security
- Validate state access in both view and model layers

### File Upload Security
- Use provided upload path functions
- Validate file extensions via `FileExtensionValidator`
- Check file size limits (5MB default in settings)

## Testing & Debugging

### Management Commands for Data Reset
```bash
python manage.py clear_data      # Clean slate for testing
python manage.py migrate         # Apply schema changes
python manage.py seed_data       # Rebuild master data
```

### Common Debug Scenarios
- State access denied → Check username pattern and UserState relationship
- Form won't save → Verify state field exclusion and manual assignment
- File upload fails → Check MEDIA_ROOT and upload path permissions
- Session issues → Review middleware order and security settings

### Key Files for Architecture Changes
- `models.py` (1821 lines) - Core business logic and validation
- `views.py` (1821 lines) - State-based access control and form handling
- `middleware.py` - Security and session management
- `forms.py` (446 lines) - Form field configuration and validation
- `settings.py` - Security headers, file upload limits, middleware order