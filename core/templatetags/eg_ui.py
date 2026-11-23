from django import template
register = template.Library()

@register.filter
def status_badge(value):
    """Map a status string to a soft-badge CSS class."""
    if not value:
        return 'badge-soft-secondary'
    v = str(value).lower()
    if v in ('active', 'approved', 'published', 'completed', 'success', 'current', 'granted'):
        return 'badge-soft-success'
    if v in ('pending', 'draft', 'submitted', 'waiting', 'review'):
        return 'badge-soft-warning'
    if v in ('rejected', 'failed', 'suspended', 'inactive', 'expired', 'deleted'):
        return 'badge-soft-danger'
    if v in ('open', 'in_progress', 'processing'):
        return 'badge-soft-info'
    return 'badge-soft-secondary'
