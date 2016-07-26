#!/bin/sh

sudo ubuntu-device-flash core 15.04 --channel edge \
    --install docker \
    --install paradrop_0.2.0_all.snap \
    --install pdinstall_0.2.0_all.snap \
    --developer-mode \
    --output paradrop_router.img
