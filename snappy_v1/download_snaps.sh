#!/bin/sh

DNSMASQ_SNAP="https://paradrop.io/storage/snaps/dnsmasq_2.74_all.snap"
HOSTAPD_SNAP="https://paradrop.io/storage/snaps/hostapd_2.4_all.snap"

if [ ! -f dnsmasq_2.74_all.snap ]; then
  wget --quiet $DNSMASQ_SNAP
fi

if [ ! -f hostapd_2.4_all.snap ]; then
  wget --quiet $HOSTAPD_SNAP
fi
