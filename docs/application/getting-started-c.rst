Getting Started with C
======================

This tutorial will teach you how to build a "Hello, World!" chute
using C and the microhttpd library.

Prerequisites
-------------

Please make sure you have pdtools v0.12.0 or newer installed.

::

    pip install pdtools~=0.12

Set up
------

Make a new directory.

::

    mkdir c-hello-world
    cd c-hello-world

Create a chute configuration
----------------------------

Use the pdtools interactive initialize command to create a paradrop.yaml
file for your chute.

::

    python -m pdtools chute initialize

Use the following values as suggested responses to the prompts. If
you have a different version of pdtools installed, the prompts may be
slightly different.

::

    name: c-hello-world
    description: Hello World chute for ParaDrop using C.
    type: normal

The end result should be a paradrop.yaml file similar to the following.

::

    description: Hello World chute for ParaDrop using C.
    name: c-hello-world
    services:
      main:
        source: .
        type: normal
    version: 1

Develop the Application
-----------------------

Create a file named ``hello.c`` with the following code. The code
for this application comes from an example file distributed with the
microhttpd library.

::

    /*
     This file is part of libmicrohttpd
     (C) 2007 Christian Grothoff (and other contributing authors)
     This library is free software; you can redistribute it and/or
     modify it under the terms of the GNU Lesser General Public
     License as published by the Free Software Foundation; either
     version 2.1 of the License, or (at your option) any later version.
     This library is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     Lesser General Public License for more details.
     You should have received a copy of the GNU Lesser General Public
     License along with this library; if not, write to the Free Software
     Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
    */

    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>

    #include <microhttpd.h>

    #define PAGE "<html><head><title>libmicrohttpd demo</title></head><body>libmicrohttpd demo</body></html>"

    static int
    ahc_echo (void *cls,
              struct MHD_Connection *connection,
              const char *url,
              const char *method,
              const char *version,
              const char *upload_data, size_t *upload_data_size, void **ptr)
    {
      static int aptr;
      const char *me = cls;
      struct MHD_Response *response;
      int ret;

      if (0 != strcmp (method, "GET"))
        return MHD_NO;              /* unexpected method */
      if (&aptr != *ptr)
        {
          /* do never respond on first call */
          *ptr = &aptr;
          return MHD_YES;
        }
      *ptr = NULL;                  /* reset when done */
      response = MHD_create_response_from_buffer (strlen (me),
                     (void *) me, MHD_RESPMEM_PERSISTENT);
      ret = MHD_queue_response (connection, MHD_HTTP_OK, response);
      MHD_destroy_response (response);
      return ret;
    }

    int
    main (int argc, char *const *argv)
    {
      struct MHD_Daemon *d;

      if (argc != 2)
        {
          printf ("%s PORT\n", argv[0]);
          return 1;
        }
      d = MHD_start_daemon (
              MHD_USE_SELECT_INTERNALLY | MHD_USE_DEBUG,
                            atoi (argv[1]),
                            NULL, NULL, &ahc_echo, PAGE,
              MHD_OPTION_CONNECTION_TIMEOUT, (unsigned int) 120,
              MHD_OPTION_END);
      if (d == NULL)
        return 1;
      pause ();
      MHD_stop_daemon (d);
      return 0;
    }

Create a file named ``Dockerfile`` with the following contents.
This project demonstrates what is called a multi-stage build
(https://docs.docker.com/develop/develop-images/multistage-build/#use-multi-stage-builds).
The first stage installs development packages for compiling the
project. The second stage merely copies the compiled binary and installs
binary shared libraries that are required in order to run the program.

::

    FROM ubuntu:16.04
    COPY hello.c .
    RUN apt-get update && apt-get install -y libmicrohttpd-dev
    RUN gcc -o hello hello.c -lmicrohttpd

    FROM ubuntu:16.04
    RUN apt-get update && apt-get install -y libmicrohttpd10
    COPY --from=0 hello /usr/bin/hello
    EXPOSE 8888
    CMD ["hello", "8888"]

Wrap Up
-------

The web server in this application listens on port 8888. We need to
include that information in the paradrop.yaml file as well. Use the
following command to alter the configuration file.

::

    python -m pdtools chute enable-web-service 8888

After that, you can continue developing the chute and install it
on a ParaDrop node.

::

    python -m pdtools node --target=<node address> install-chute
