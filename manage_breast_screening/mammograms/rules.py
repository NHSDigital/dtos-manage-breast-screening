"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.auth.rules import is_clinical

rules.add_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT, is_clinical)
rules.add_perm(Permission.DO_MAMMOGRAM_APPOINTMENT, is_clinical)
