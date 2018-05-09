"""
Configure optional additional services such as telemetry.
"""
from paradrop.core.agent import reporting
from paradrop.lib.utils import datastruct

from twisted.internet.task import LoopingCall


telemetry_looping_call = None


def configure_telemetry(update):
    global telemetry_looping_call

    hostConfig = update.cache_get('hostConfig')

    enabled = datastruct.getValue(hostConfig, 'telemetry.enabled', False)
    interval = datastruct.getValue(hostConfig, 'telemetry.interval', 60)

    # Cancel the old looping call.
    if telemetry_looping_call is not None:
        telemetry_looping_call.stop()
        telemetry_looping_call = None

    if enabled and interval > 0:
        telemetry_looping_call = LoopingCall(reporting.sendTelemetryReport)
        telemetry_looping_call.start(interval, now=False)
