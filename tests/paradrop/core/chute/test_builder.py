import yaml

from paradrop.core.chute import builder


TEST_CHUTE = """
name: seccam
description: A Paradrop chute that performs motion detection using a simple WiFi camera.
version: 1

services:
 main:
   type: light
   source: .
   image: python2
   command: python -u seccam.py

   environment:
     IMAGE_INTERVAL: 2.0
     MOTION_THRESHOLD: 40.0
     SECCAM_MODE: detect

   interfaces:
     wlan0:
       type: wifi-ap

       dhcp:
         leasetime: 12h
         limit: 250
         start: 4

       wireless:
         ssid: seccam42
         key: paradropseccam
         hidden: false
         isolate: true

       requirements:
         hwmode: 11g

   requests:
     as-root: true
     port-bindings:
       - external: 81
         internal: 81

 db:
   type: image
   image: mongo:3.0

web:
 service: main
 port: 5000
"""


def test_build_chute():
    config = yaml.safe_load(TEST_CHUTE)
    chute = builder.build_chute(config)

    assert chute.name == "seccam"

    services = chute.get_services()
    assert len(services) == 2

    main = chute.get_service("main")
    assert main.name == "main"
    assert main.type == "light"

    assert main.environment["SECCAM_MODE"] == "detect"
