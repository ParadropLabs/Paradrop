#!/bin/sh

sudo ubuntu-device-flash core 15.04 --channel stable \
    --install docker \
    --install paradrop_0.2.0_all.snap \
    --install pdinstall_0.2.0_all.snap \
    --install dnsmasq_2.74_all.snap \
    --install hostapd_2.4-1_all.snap \
    --developer-mode \
    --output paradrop_router.img
