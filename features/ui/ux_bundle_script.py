"""Aggregator bundling modular UX scripts so script.py stays well below its line ceiling."""

from features.ui.agent_builder_script import AGENT_BUILDER_SCRIPT
from features.ui.comfort_script import COMFORT_SCRIPT
from features.ui.command_script import COMMAND_SCRIPT
from features.ui.eco_sync_script import ECO_SYNC_SCRIPT
from features.ui.editor_script import EDITOR_SCRIPT
from features.ui.guide_script import GUIDE_SCRIPT
from features.ui.mention_script import MENTION_SCRIPT
from features.ui.power_script import POWER_SCRIPT
from features.ui.study_script import STUDY_SCRIPT
from features.ui.work_board_script import WORK_BOARD_SCRIPT
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
    + AGENT_BUILDER_SCRIPT
    + WORK_BOARD_SCRIPT
    + r"""
function bindAllUXBundles() {
  for (const fn of [
    typeof bindComfortControls === "function" && bindComfortControls,
    typeof bindCommandUX === "function" && bindCommandUX,
    typeof bindMentionUX === "function" && bindMentionUX,
    typeof bindEditorUX === "function" && bindEditorUX,
    typeof bindWorkflowUX === "function" && bindWorkflowUX,
    typeof bindStudyUX === "function" && bindStudyUX,
    typeof bindEcoSyncUX === "function" && bindEcoSyncUX,
    typeof bindPowerUX === "function" && bindPowerUX,
    typeof bindGuideUX === "function" && bindGuideUX,
    typeof bindAgentBuilderUX === "function" && bindAgentBuilderUX,
    typeof bindWorkBoardUX === "function" && bindWorkBoardUX,
  ]) {
    if (fn) { try { fn(); } catch (err) { console.error("UX bundle init failed:", err); } }
  }
}
"""
)
