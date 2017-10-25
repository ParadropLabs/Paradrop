from mock import MagicMock
from nose.tools import assert_raises

from paradrop.confd import wireless
from paradrop.confd.wireless import ConfigWifiIface, HostapdConfGenerator


def test_get_cipher_list():
    assert wireless.get_cipher_list("psk2+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk2+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk2+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("psk2+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("psk2+aes") == ["CCMP"]
    assert wireless.get_cipher_list("psk2") == ["CCMP"]

    assert wireless.get_cipher_list("psk+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("psk+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("psk+aes") == ["CCMP"]
    assert wireless.get_cipher_list("psk") == ["CCMP"]

    assert wireless.get_cipher_list("psk-mixed+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk-mixed+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("psk-mixed+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("psk-mixed+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("psk-mixed+aes") == ["CCMP"]
    assert wireless.get_cipher_list("psk-mixed") == ["CCMP"]

    assert wireless.get_cipher_list("wpa2+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa2+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa2+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("wpa2+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("wpa2+aes") == ["CCMP"]
    assert wireless.get_cipher_list("wpa2") == ["CCMP"]

    assert wireless.get_cipher_list("wpa+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("wpa+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("wpa+aes") == ["CCMP"]
    assert wireless.get_cipher_list("wpa") == ["TKIP"]

    assert wireless.get_cipher_list("wpa-mixed+tkip+ccmp") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa-mixed+tkip+aes") == ["TKIP", "CCMP"]
    assert wireless.get_cipher_list("wpa-mixed+tkip") == ["TKIP"]
    assert wireless.get_cipher_list("wpa-mixed+ccmp") == ["CCMP"]
    assert wireless.get_cipher_list("wpa-mixed+aes") == ["CCMP"]
    assert wireless.get_cipher_list("wpa-mixed") == ["CCMP"]


def test_ConfigWifiIface_apply():
    """
    Test the ConfigWifiIface apply method
    """
    wifiDevice = MagicMock()
    interface = MagicMock()

    allConfigs = {
        ("wireless", "wifi-device", "phy0"): wifiDevice,
        ("network", "interface", "lan"): interface
    }

    config = ConfigWifiIface()
    config.manager = MagicMock()
    config.makeHostapdConf = MagicMock()

    config.device = "phy0"
    config.mode = "ap"
    config.ssid = "Paradrop"
    config.network = "lan"
    config.encryption = "psk2"
    config.key = "password"

    wifiDevice.name = "phy0"
    interface.config_ifname = "wlan0"

    commands = config.apply(allConfigs)


def test_HostapdConfGenerator_getMainOptions():
    wifiIface = MagicMock()
    wifiIface.ssid = "Paradrop"
    wifiIface.maxassoc = 200
    wifiIface.wmm = True
    wifiIface._ifname = "wlan0"

    wifiDevice = MagicMock()
    wifiDevice.country = "US"
    wifiDevice.hwmode = "11a"
    wifiDevice.channel = 36
    wifiDevice.beacon_int = 100
    wifiDevice.rts = -1
    wifiDevice.frag = -1

    interface = MagicMock()
    interface.type = "bridge"
    interface.config_ifname = "br-lan"

    generator = HostapdConfGenerator(wifiIface, wifiDevice, interface)

    options = generator.getMainOptions()
    print(options)
    assert ("interface", "wlan0") in options
    assert ("bridge", "br-lan") in options
    assert ("ssid", "Paradrop") in options
    assert ("country_code", "US") in options
    assert ("ieee80211d", 1) in options
    assert ("hw_mode", "a") in options
    assert ("beacon_int", 100) in options
    assert ("max_num_sta", 200) in options
    assert ("rts_threshold", -1) in options
    assert ("fragm_threshold", -1) in options
    assert ("wmm_enabled", 1) in options


def test_HostapdConfGenerator_get11nOptions():
    wifiDevice = MagicMock()
    wifiDevice.enable11n = True
    wifiDevice.htmode = "HT40+"
    wifiDevice.short_gi_20 = True
    wifiDevice.short_gi_40 = True
    wifiDevice.tx_stbc = 1
    wifiDevice.rx_stbc = 2
    wifiDevice.dsss_cck_40 = True
    wifiDevice.require_mode = "n"

    wifiIface = MagicMock()
    interface = MagicMock()

    generator = HostapdConfGenerator(wifiIface, wifiDevice, interface)

    options = generator.get11nOptions()
    options = dict(options)
    print(options)
    assert "HT40+" in options['ht_capab']
    assert options['ieee80211n'] == 1
    assert options['require_ht'] == 1

    # Enabling 11ac (VHT80) and using channel 40 should configure HT40- mode
    # for 11n clients.
    wifiDevice.htmode = "VHT80"
    wifiDevice.channel = 40

    options = generator.get11nOptions()
    options = dict(options)
    print(options)
    assert "HT40-" in options['ht_capab']

    # Enabling 11ac (VHT80) and using channel 36 should configure HT40+ mode
    # for 11n clients.
    wifiDevice.htmode = "VHT80"
    wifiDevice.channel = 36

    options = generator.get11nOptions()
    options = dict(options)
    print(options)
    assert "HT40+" in options['ht_capab']


def test_HostapdConfGenerator_get11acOptions():
    wifiDevice = MagicMock()
    wifiDevice.enable11ac = True
    wifiDevice.htmode = "VHT40"
    wifiDevice.short_gi_80 = True
    wifiDevice.short_gi_160 = True
    wifiDevice.tx_stbc = 1
    wifiDevice.rx_stbc = 2
    wifiDevice.require_mode = "ac"
    wifiDevice.channel = 36

    wifiIface = MagicMock()
    interface = MagicMock()

    generator = HostapdConfGenerator(wifiIface, wifiDevice, interface)

    options = generator.get11acOptions()
    print(options)
    assert ("ieee80211ac", 1) in options
    assert ("vht_capab", "[RXLDPC][SHORT-GI-80][SHORT-GI-160][TX-STBC-2BY1][RX-ANTENNA-PATTERN][TX-ANTENNA-PATTERN][RX-STBC-12]") in options
    assert ("vht_oper_chwidth", 0) in options
    assert ("vht_oper_centr_freq_seg0_idx", 38) in options

    # Try 80 MHz channel.
    wifiDevice.htmode = "VHT80"
    options = generator.get11acOptions()
    assert ("vht_oper_chwidth", 1) in options
    assert ("vht_oper_centr_freq_seg0_idx", 42) in options

    # Try 160 MHz channel.
    wifiDevice.htmode = "VHT160"
    options = generator.get11acOptions()
    assert ("vht_oper_chwidth", 2) in options
    assert ("vht_oper_centr_freq_seg0_idx", 50) in options


def test_HostapdConfGenerator_getRadiusOptions():
    wifiIface = ConfigWifiIface()
    wifiIface.ssid = "Paradrop"
    wifiIface.maxassoc = 200
    wifiIface.wmm = True
    wifiIface.ifname = "wlan0"
    wifiIface.auth_server = "10.42.0.1"
    wifiIface.auth_secret = "secret"
    wifiIface.acct_server = "10.42.0.1"
    wifiIface.acct_secret = "secret"

    wifiDevice = MagicMock()
    wifiDevice.country = "US"
    wifiDevice.hwmode = "11a"
    wifiDevice.channel = 36
    wifiDevice.beacon_int = 100
    wifiDevice.rts = -1
    wifiDevice.frag = -1

    interface = MagicMock()
    interface.type = "bridge"
    interface.config_ifname = "br-lan"

    generator = HostapdConfGenerator(wifiIface, wifiDevice, interface)

    options = generator.getRadiusOptions()
    print(options)


def test_HostapdConfGenerator_get11rOptions():
    wifiIface = ConfigWifiIface()
    wifiIface.r0kh = [
        "02:01:02:03:04:05 r0kh-1.example.com 000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f",
        "02:01:02:03:04:06 r0kh-2.example.com 00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
    ]
    wifiIface.r1kh = [
        "00:00:00:00:00:00 00:00:00:00:00:00 00112233445566778899aabbccddeeff"
    ]

    wifiDevice = MagicMock()
    interface = MagicMock()

    generator = HostapdConfGenerator(wifiIface, wifiDevice, interface)

    # Should raise an exception because nasid is not set.
    assert_raises(Exception, generator.get11rOptions)

    wifiIface.nasid = "ap.example.com"

    options = generator.get11rOptions()

    # There should be two r0kh entries and one r1kh entry.
    assert sum(k[0] == 'r0kh' for k in options) == 2
    assert sum(k[0] == 'r1kh' for k in options) == 1
