from paradrop.backend.exc import traffic
from mock import patch, MagicMock
from paradrop.lib import config
from paradrop.backend.exc import plangraph


@patch('paradrop.backend.exc.runtime.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    update = MagicMock()
    update.plans.addPlans.side_effect = [Exception('e'), None, Exception('e'), None, None, None]
    todoPlan = (config.configservice.reloadAll, )
    abtPlan = [(config.osconfig.revertConfig, "dhcp"),
               (config.osconfig.revertConfig, "firewall"),
               (config.osconfig.revertConfig, "network"),
               (config.osconfig.revertConfig, "wireless"),
               (config.configservice.reloadAll, )]
    def c1():
        update.plans.addPlans.assert_called_with(plangraph.TRAFFIC_GET_OS_FIREWALL, (config.firewall.getOSFirewallRules, ))
    def c2():
        update.plans.addPlans.assert_called_with(plangraph.TRAFFIC_GET_DEVELOPER_FIREWALL, (config.firewall.getDeveloperFirewallRules, ))
    def c3():
        todoPlan = (config.firewall.setOSFirewallRules, )
        abtPlan = (config.osconfig.revertConfig, "firewall")
        update.plans.addPlans.assert_called_with(plangraph.TRAFFIC_SET_OS_FIREWALL, todoPlan, abtPlan)
    for call in [c1, c2, c3]:
        try:
            traffic.generatePlans(update)
        except Exception as e:
            pass
        call()
