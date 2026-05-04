# Import model modules so SQLAlchemy registers all Table objects on Base.metadata.
# Keep imports as module-level (or `from ... import ...  # noqa: F401`) to avoid unused-import warnings.

import app.models.application
import app.models.associations  # registers user_roles, role_permissions, etc.
import app.models.audit
import app.models.background_check
import app.models.client
import app.models.document
import app.models.invitation
import app.models.notification
import app.models.report
import app.models.role
import app.models.service_request
import app.models.task
import app.models.user
import app.models.vettingForm
