"""Aggregator bundling modular UX scripts so script.py stays well below its line ceiling."""

from features.ui.comfort_script import COMFORT_SCRIPT
from features.ui.command_script import COMMAND_SCRIPT
from features.ui.eco_sync_script import ECO_SYNC_SCRIPT
from features.ui.editor_script import EDITOR_SCRIPT
from features.ui.guide_script import GUIDE_SCRIPT
from features.ui.mention_script import MENTION_SCRIPT
from features.ui.power_script import POWER_SCRIPT
from features.ui.study_script import STUDY_SCRIPT
from features.ui.workflow_script import WORKFLOW_SCRIPT

UX_BUNDLE_SCRIPT: str = (
    COMFORT_SCRIPT
    + COMMAND_SCRIPT
    + MENTION_SCRIPT
    + EDITOR_SCRIPT
    + WORKFLOW_SCRIPT
    + STUDY_SCRIPT
    + ECO_SYNC_SCRIPT
    + POWER_SCRIPT
    + GUIDE_SCRIPT
    + r"""
function bindAllUXBundles() {
  if (typeof bindComfortControls === "function") { bindComfortControls(); }
  if (typeof bindCommandUX === "function") { bindCommandUX(); }
  if (typeof bindMentionUX === "function") { bindMentionUX(); }
  if (typeof bindEditorUX === "function") { bindEditorUX(); }
  if (typeof bindWorkflowUX === "function") { bindWorkflowUX(); }
  if (typeof bindStudyUX === "function") { bindStudyUX(); }
  if (typeof bindEcoSyncUX === "function") { bindEcoSyncUX(); }
  if (typeof bindPowerUX === "function") { bindPowerUX(); }
  if (typeof bindGuideUX === "function") { bindGuideUX(); }
}
"""
)
