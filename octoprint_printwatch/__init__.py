from __future__ import absolute_import, unicode_literals
import octoprint.plugin
from octoprint.events import Events
from .utils.videostreamer import VideoStreamer
from .utils.comm import CommManager
from .utils.inferencer import Inferencer
from .utils.printer import PrinterControl
import os

class PrintWatchPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.ShutdownPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.EventHandlerPlugin
                           ):


    def on_after_startup(self):
        with open(os.path.join(os.path.dirname(__file__), 'data/unique_identifier.txt'), 'r') as f:
            self.id = f.read()
        self._logger.info("Loading PrintWatch...")
        self.comm_manager = CommManager(self)
        self.streamer = VideoStreamer(self)
        self.inferencer = Inferencer(self)
        self.controller = PrinterControl(self)


    def get_update_information(self):
        return dict(
            PrintWatch=dict(
                name="PrintWatch",
                version=self._plugin_version)
                )


    def get_settings_defaults(self):
        return dict(
            stream_url = "http://127.0.0.1/webcam/?action=stream",
            enable_detector = True,
            enable_email_notification = False,
            email_addr = '',
            enable_shutoff = False,
            confidence = 60,
            enable_feedback_images = True,
            api_key = ''
            )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]


    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self.streamer.start_service()
            self.inferencer.start_service()
        elif event == Events.PRINT_RESUMED:
            if self.inferencer.triggered:
                self.controller.restart()
            self.streamer.start_service()
            self.inferencer.start_service()
        elif event in (
            Events.PRINT_PAUSED,
            Events.PRINT_CANCELLED,
            Events.PRINT_DONE,
            Events.PRINT_FAILED
            ):
            if self.inferencer.triggered:
                self.inferencer.shutoff_event()
            self.inferencer.kill_service()
            self.streamer.kill_service()



    def on_shutdown(self):
        self.inferencer.run_thread = False
        self.streamer.stream_enabled = False



__plugin_name__ = "PrintWatch"
__plugin_version__ = "1.0.10"
__plugin_description__ = "PrintWatch watches your prints for defects and optimizes your 3D printers using Artificial Intelligence."
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = PrintWatchPlugin()


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrintWatchPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }