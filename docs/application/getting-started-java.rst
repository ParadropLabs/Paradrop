Getting Started with Java
=========================

This tutorial will teach you how to build a "Hello, World!" chute using
Java and Maven.

Prerequisites
-------------

Make sure you have Java 1.8+, Maven 3.0+, as well as ParaDrop pdtools
(v0.12.0 or newer).

::

    pip install pdtools~=0.12

Set up
------

Use Maven to set up an empty project.

::

    mvn archetype:generate -DgroupId=org.paradrop.app -DartifactId=java-hello-world -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false
    cd java-hello-world

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

    name: java-hello-world
    description: Hello World chute for ParaDrop using Java.
    type: light
    image: maven
    command: java -cp target/java-hello-world-1.0-SNAPSHOT.jar org.paradrop.app.App

The end result should be a paradrop.yaml file similar to the following.

::

    description: Hello World chute for ParaDrop using Java.
    name: java-hello-world
    services:
      main:
        command: java -cp target/java-hello-world-1.0-SNAPSHOT.jar org.paradrop.app.App
        image: maven
        source: .
        type: light
    version: 1

Develop the Application
-----------------------

Replace the automatically-generated application code in
``src/main/java/org/paradrop/app/App.java`` with the following code.

::

    package org.paradrop.app;

    import java.io.IOException;
    import java.io.OutputStream;
    import java.net.InetSocketAddress;

    import com.sun.net.httpserver.HttpExchange;
    import com.sun.net.httpserver.HttpHandler;
    import com.sun.net.httpserver.HttpServer;

    public class App {
        public static void main(String[] args) throws Exception {
            System.out.println("Listening on :8000");
            HttpServer server = HttpServer.create(new InetSocketAddress(8000), 0);
            server.createContext("/", new GetIndex());
            server.start();
        }

        static class GetIndex implements HttpHandler {
            @Override
            public void handle(HttpExchange t) throws IOException {
                String response = "Hello, World!";
                t.sendResponseHeaders(200, response.length());
                OutputStream os = t.getResponseBody();
                os.write(response.getBytes());
                os.close();
            }
        }
    }

Run the application locally with the following commands.

::

    mvn package
    java -cp target/java-hello-world-1.0-SNAPSHOT.jar org.paradrop.app.App

Then load ``http://localhost:8000/`` in a web browser to see the result.

Wrap Up
-------

The web server in this application listens on port 8000. We need to
include that information in the paradrop.yaml file as well. Use the
following command to alter the configuration file.

::

    python -m pdtools chute enable-web-service 8000

After that, you can continue developing the chute and install it
on a ParaDrop node.

::

    python -m pdtools node --target=<node address> install-chute
