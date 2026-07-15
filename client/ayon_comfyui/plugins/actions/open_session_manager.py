from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import functools
import urllib.parse

# IMPORT THIRD-PARTY LIBRARIES
import ayon_api
from ayon_core.lib import get_settings_variant
from ayon_core.pipeline.actions.launcher import LauncherAction, LauncherActionSelection
from ayon_core.lib.icon_definitions import PathIcon
from ayon_applications.addon import ApplicationsAddon

# IMPORT LOCAL LIBRARIES
from ayon_comfyui.constants import COMFYUI_ICON_PATH_SVG


@functools.cache
def get_applications_items(project_name: str, task_id: str) -> list[dict]:
    """based on ApplicationsAddon.get_application_items

    The version in `ayon_applications` requires 1.4.3+,
    and also has some changes which are not deployed yet.
    So to keep things compatible we reimplement the function here.

    """
    variant = get_settings_variant()

    query_params = {"variant": variant}
    query = urllib.parse.urlencode(query_params)

    response = ayon_api.get(
        f"addons/{ApplicationsAddon.name}/{ApplicationsAddon.version}/"
        f"apps/{project_name}/task/{task_id}?{query}"
    )
    return response.data.get("applications", [])


class OpenSessionManager(LauncherAction):
    """Open AYON browser page to the current context."""
    name = "open_session_manager"
    label = "Session Manager"
    icon = PathIcon(str(COMFYUI_ICON_PATH_SVG))
    order = 999

    def _get_hosts_for_selection(self, selection: LauncherActionSelection) -> set[str]:
        items = get_applications_items(
            project_name=selection.project_name,
            task_id=selection.task_id,
        )
        return {name for item in items if (name := item.get("host_name"))}

    def is_compatible(self, selection: LauncherActionSelection) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        hosts = self._get_hosts_for_selection(selection)
        return "comfyui" in hosts

    def process(self, selection, **kwargs):
        print("Hello!")
