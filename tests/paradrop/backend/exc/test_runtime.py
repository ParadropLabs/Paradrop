from paradrop.backend.exc import runtime
from mock import patch, MagicMock
from paradrop.lib import config
from paradrop.backend.exc import plangraph


@patch('paradrop.backend.exc.runtime.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    update = MagicMock()
    update.plans.addPlans.side_effect = [Exception('e'), None, Exception('e'), None, None, Exception('e'), None, None, None, None]
    todoPlan = (config.configservice.reloadAll, )
    abtPlan = [(config.osconfig.revertConfig, "dhcp"),
               (config.osconfig.revertConfig, "firewall"),
               (config.osconfig.revertConfig, "network"),
               (config.osconfig.revertConfig, "wireless"),
               (config.configservice.reloadAll, )]
    def c1():
        update.plans.addPlans.assert_called_with(plangraph.RUNTIME_GET_VIRT_PREAMBLE, (config.dockerconfig.getVirtPreamble, ))
    def c2():
        update.plans.addPlans.assert_called_with(plangraph.RUNTIME_GET_VIRT_DHCP, (config.dhcp.getVirtDHCPSettings, ))
    def c3():
        update.plans.addPlans.assert_called_with(plangraph.RUNTIME_SET_VIRT_DHCP, (config.dhcp.setVirtDHCPSettings, ))
    def c4():
        update.plans.addPlans.assert_called_with(plangraph.RUNTIME_RELOAD_CONFIG, todoPlan, abtPlan)
    for call in [c1, c2, c3, c4]:
        try:
            runtime.generatePlans(update)
        except Exception as e:
            pass
        call()
