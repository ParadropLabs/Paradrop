Tutorial: Sticky Board
======================

This tutorial will teach you how to build a fully-functional ParaDrop
application from scratch.  Through the tutorial, we will build a "Sticky
Board", a local board where visitors can post images for others to see.
We will be using Node.js to build the application, so make sure you have
that installed on your development machine.

Set Up
------

Make a new directory, and initialize a git repository::

    mkdir sticky_board
    cd sticky_board
    git init
    mkdir views

Setup Node.js Project
---------------------

We will be using npm to manage Node.js packages.  You can use the
``npm init`` command to get started or create a file called package.json.
with the following contents::

    {
      "name": "sticky_board",
      "version": "1.0.0",
      "description": "Post images for others to see.",
      "main": "index.js",
      "author": "ParaDrop Team"
    }

Install Dependencies
--------------------

Use the following command to install some dependencies that we will be
using to build the application.  We use express as a simple web server
along with a plugin for accepting file uploads.  We will also use Embedded
JS (EJS) for simple templating, demonstrated later in this tutorial.

The ``--save`` option instructs npm to save the packages to the package.json
file.  ParaDrop will read package.json to install the same versions of
the packages that you used for development.

::

    npm install --save ejs@^2.5.6 express@^4.14.1 express-fileupload@^0.1.1

Hello World
-----------

Let's start with a minimal Hello World Express.js example.  Create a file
named ``index.js`` and add the following code::

    var express = require('express');
    var app = express();

    app.get('/', function (req, res) {
      res.send('Hello World!');
    });

    app.listen(3000, function() {
      console.log('Listening on port 3000.');
    });

Run the app with the following command::

    node index.js

Then load ``http://localhost:3000/`` in a web browser to see the result.

Image Uploads
-------------

Next, we will add an endpoint to receive image uploads.

::

    var express = require('express');
    var fileupload = require('express-fileupload');

    var app = express();

    // Use PARADROP_DATA_DIR when running on Paradrop and /tmp for testing.
    var storage_dir = process.env.PARADROP_DATA_DIR || '/tmp';

    app.use(fileupload());
    app.use(express.static(storage_dir));
    app.set('view engine', 'ejs');

    app.post('/create', function(req, res) {
      var img = req.files.img;
      if (img) {
        img.mv(storage_dir + '/' + img.name);
      }

      res.redirect('/');
    });

    app.get('/', function (req, res) {
      res.render('home');
    });

    app.listen(3000, function() {
      console.log('Listening on port 3000.');
    });

Create a new file in the views directory called home.ejs with the following
contents::

    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>ParaDrop Sticky Board</title>
      </head>
      <body>
        <h1>ParaDrop Sticky Board</h1>
        <h2>Create a Note</h2>
        <p>Upload an image file to create a note for others to see.</p>
        <form action="/create" method="POST" encType="multipart/form-data">
          <input type="file" name="img" />
          <input type="submit" value="Create" />
        </form>
      </body>
    </html>

Right now it is just plain HTML.  In the next section we will make use of
templating to add images to the sticky board.

Run the app again and load ``http://localhost:3000/``.  Try using the
form to upload an image.  You should then be able to find your image
by loading ``http://localhost:3000/<filename>``.

Displaying Notes
----------------

The last thing the app needs to be able to do is display all of the
notes that people have posted.  First, add some logic to index.js
to keep track of the most recent image uploads::

    var express = require('express');
    var fileupload = require('express-fileupload');

    var app = express();

    // Use PARADROP_DATA_DIR when running on Paradrop and /tmp for testing.
    var storage_dir = process.env.PARADROP_DATA_DIR || '/tmp';

    // Maximum number of notes to display.
    var max_visible_notes = process.env.MAX_VISIBLE_NOTES || 16;

    app.locals.notes = [];
    for (var i = 0; i < max_visible_notes; i++) {
      if (i % 2 == 0) {
        addNote('http://pages.cs.wisc.edu/~hartung/paradrop/paradrop.png');
      } else {
        addNote('http://pages.cs.wisc.edu/~hartung/paradrop/paradrop_inverted.png');
      }
    }

    function addNote(img) {
      app.locals.notes.push({
        img: img,
      });

      if (app.locals.notes.length > max_visible_notes) {
        app.locals.notes = app.locals.notes.slice(-max_visible_notes);
      }
    }

    app.use(fileupload());
    app.use(express.static(storage_dir));
    app.set('view engine', 'ejs');

    app.post('/create', function(req, res) {
      var img = req.files.img;
      if (img) {
        img.mv(storage_dir + '/' + img.name);
        addNote(img.name);
      }

      res.redirect('/');
    });

    app.get('/', function (req, res) {
      res.render('home');
    });

    app.listen(3000, function() {
      console.log('Listening on port 3000.');
    });


The paradrop.png and paradrop_inverted.png are just used as fillers
until people post other images.  Feel free to use different images.

Also, update home.ejs::

    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>ParaDrop Sticky Board</title>

        <style>
          div.holder {
            float: left;
            min-width: 240px;
            width: 24%;
            padding: 5px 5px;
          }

          div.separator {
            clear: both;
          }
        </style>
      </head>
      <body>
        <h1>ParaDrop Sticky Board</h1>

        <div>
          <% for(var i = 0; i<notes.length; i++) {%>
            <div class="holder">
              <img src="<%= notes[i].img %>" width="100%"></img>
            </div>
          <% } %>
        </div>

        <div class="separator"></div>

        <h2>Create a Note</h2>
        <p>Upload an image file to create a note for others to see.</p>
        <form action="/create" method="POST" encType="multipart/form-data">
          <input type="file" name="img" />
          <input type="submit" value="Create" />
        </form>
      </body>
    </html>

We use some Embedded JS code to loop over the array of notes stored
in ``app.locals.notes`` and generate an img element for each one with
the appropriate filename.

Now when you run the app and load ``http://localhost:3000/`` you should
see the filler images.  Try using the form to upload an image, and
it should appear on the board.

Preparing the Chute
-------------------

Create a file called paradrop.yaml with the following contents::

    name: sticky-board
    description: Run a local bulletin board where guests can post images.
    version: 1

    services:
      main:
        type: light
        use: node
        command: node index.js

    web:
      service: main
      port: 3000

This file tells ParaDrop a few things about how to run your code
on a ParaDrop gateway.

Finally, add all of your new files to the git repository::

    git add index.js package.json paradrop.yaml views/home.ejs
    git commit -m "Created sticky board from tutorial"

Create a new repository on github.com and follow their instructions
to push your code to github.

Registering the Chute with ParaDrop
-----------------------------------

Log on to paradrop.org and go to the Chute Store tab.  Click "Create Chute"
and give your chute a name and description.  You may need to be creative
with the name because the chute store requires unique names.  Then click
"Submit".

Next, click "Create Version".  For this tutorial, there are only two
important fields to fill out on this form.  First, check the box
to "enable web service" and enter the number 3000 because that is the
port we chose in index.js.  Second, select "Download from URL"
for Project source and enter the github URL for your project.  Then
click "Submit".

Congratulations!  You have made a ParaDrop chute.  If you have a
ParaDrop router, you should now be able to install the chute on
your router.  If not, you can follow the Getting Started guide to
set up a VM running ParaDrop.
