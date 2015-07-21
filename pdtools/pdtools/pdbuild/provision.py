'''
Router provisioning

NOTE: In writing this code Ive come to believe its easier and better
for us to host pre-installed and provisioned instances ourselves rather 
than build them from scratch.

We would host the image with all tools installed then provide it 
for download. How the provisioning process actually occurs I'm not sure. 
'''

import subprocess
import os
import wget


def provisionVirtual():
    '''
    Provision a virtual machine with snappy and paradrop.

        - Downloads the snappy vm and paradrop.snap, or takes a directory from which 
    to build paradrop.snap from. 
        - Mounts the VM and inserts keys and identifying information from the server. 
        - Unmount the image and remove the mounting directory  
    '''
    pass


def provisionHardware():
    '''
    Provision a physical machine with snappy and paradrop.

        - Downloads the snappy vm and paradrop.snap, or takes a directory from which 
    to build paradrop.snap from. 
        - Flashes snappy onto the target disk
        - Inserts keys and identifying information from the server. 
        - Unmount the image and remove the mounting directory  
    '''
    pass


def partedtest():

    path = os.path.dirname(os.getcwd()) + '/snappy-vm.img'

    # Get the offset
    output = subprocess.check_output("parted -s " + path + " unit B print", shell=True)
    target = [x for x in output.split('\n') if 'system-a' in x][0]

    # The second entry is the target offset, but this may not be kosher...
    offset = target.split()[1].replace('B', '')

    # Mount (this may not be necesary when provisioning flashed router)
    mountdir = '/mnt/snappytmp'
    output = subprocess.check_output("sudo mkdir " + mountdir, shell=True)
    output = subprocess.check_output("sudo mount -o loop,offset=%s %s %s" % (offset, path, mountdir), shell=True)


def cleanup():
    try:
        subprocess.check_output("sudo umount " + mountdir, shell=True)
    except:
        print 'Done'

###############################################################################
#  Downloading
###############################################################################


def downloadImage(defaultPath):
    '''
    Download a snappy image
    '''
    url = 'http://releases.ubuntu.com/15.04/ubuntu-15.04-snappy-amd64-generic.img.xz'

    path = raw_input("Enter a directory to save the image [" + defaultPath + ']') or defaultPath

    # Check and see if an image already exists
    # Ask the user if they want to save to a custom directory
    # Download the image
