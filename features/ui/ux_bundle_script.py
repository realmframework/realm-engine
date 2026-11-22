"""Aggregator bundling modular UX scripts so script.py stays well below its line ceiling."""

from features.ui.agent_builder_script import AGENT_BUILDER_SCRIPT
from features.ui.comfort_script import COMFORT_SCRIPT
from features.ui.command_script import COMMAND_SCRIPT
from features.ui.copilot_controls_script import COPILOT_CONTROLS_SCRIPT
from features.ui.copilot_script import COPILOT_SCRIPT
from features.ui.eco_sync_script import ECO_SYNC_SCRIPT
from features.ui.editor_script import EDITOR_SCRIPT
from features.ui.file_tab_script import FILE_TAB_SCRIPT
from features.ui.focus_script import FOCUS_SCRIPT
from features.ui.guide_script import GUIDE_SCRIPT
from features.ui.impact_script import IMPACT_SCRIPT
from features.ui.local_ai_script import LOCAL_AI_SCRIPT
from features.ui.mention_script import MENTION_SCRIPT
from features.ui.power_script import POWER_SCRIPT
from features.ui.shell_script import SHELL_SCRIPT
from features.ui.split_script import SPLIT_SCRIPT
from features.ui.study_script import STUDY_SCRIPT
from features.ui.work_board_script import WORK_BOARD_SCRIPT
from features.ui.workbench_tabs_script import WORKBENCH_TABS_SCRIPT
from features.ui.workflow_canvas_script import WORKFLOW_CANVAS_SCRIPT
from features.ui.workflow_run_script import WORKFLOW_RUN_SCRIPT
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
    + SPLIT_SCRIPT
    + FOCUS_SCRIPT
    + IMPACT_SCRIPT
    + WORKFLOW_CANVAS_SCRIPT
    + WORKFLOW_RUN_SCRIPT
    + SHELL_SCRIPT
    + WORKBENCH_TABS_SCRIPT
    + FILE_TAB_SCRIPT
    + COPILOT_CONTROLS_SCRIPT
    + COPILOT_SCRIPT
    + LOCAL_AI_SCRIPT
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
    typeof bindSplitUX === "function" && bindSplitUX,
    typeof bindFocusUX === "function" && bindFocusUX,
    typeof bindImpactUX === "function" && bindImpactUX,
    typeof bindWorkflowStudioUX === "function" && bindWorkflowStudioUX,
    typeof bindSpatialShellUX === "function" && bindSpatialShellUX,
    typeof bindWorkbenchTabsUX === "function" && bindWorkbenchTabsUX,
    typeof bindFileTabUX === "function" && bindFileTabUX,
    typeof bindCopilotControlsUX === "function" && bindCopilotControlsUX,
    typeof bindCopilotUX === "function" && bindCopilotUX,
    typeof bindLocalAiUX === "function" && bindLocalAiUX,
  ]) {
    if (fn) { try { fn(); } catch (err) { console.error("UX bundle init failed:", err); } }
  }
}
"""
)
