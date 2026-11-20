"""Compose bounded area, governance and confirmation scripts."""

from features.ui.area_script import AREA_SCRIPT
from features.ui.confirm_script import CONFIRM_SCRIPT
from features.ui.redaction_script import REDACTION_SCRIPT

INTERACTION_SCRIPT = AREA_SCRIPT + CONFIRM_SCRIPT + REDACTION_SCRIPT
