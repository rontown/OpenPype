from . import PypeModule, ITrayAction


class ProjectManagerAction(PypeModule, ITrayAction):
    label = "Project Manager"
    name = "project_manager"
    admin_action = True

    def initialize(self, _modules_settings):
        # This action is always enabled
        self.enabled = True

        # Tray attributes
        self.project_manager_window = None

    def connect_with_modules(self, *_a, **_kw):
        return

    def tray_init(self):
        """Initialization in tray implementation of ITrayAction."""
        self.create_project_manager_window()

    def on_action_trigger(self):
        """Implementation for action trigger of ITrayAction."""
        self.show_project_manager_window()

    def create_project_manager_window(self):
        """Initializa Settings Qt window."""
        if self.project_manager_window:
            return
        from openpype.tools.project_manager import ProjectManagerWindow

        self.project_manager_window = ProjectManagerWindow()

    def show_project_manager_window(self):
        """Show project manager tool window.

        Raises:
            AssertionError: Window must be already created. Call
                `create_project_manager_window` before calling this method.
        """
        if not self.project_manager_window:
            raise AssertionError("Window is not initialized.")

        # Store if was visible
        was_minimized = self.project_manager_window.isMinimized()

        # Show settings gui
        self.project_manager_window.show()

        if was_minimized:
            self.project_manager_window.showNormal()

        # Pull window to the front.
        self.project_manager_window.raise_()
        self.project_manager_window.activateWindow()
