Documentation and tests
====================================

Documentation is handled by `sphinx <http://sphinx-doc.org/>`_ and readthedocs.

Testing is a joint effort between `nosetests <https://nose.readthedocs.org/en/latest/>`_, travis-ci, and coveralls. 


Documentation
--------------
Information about docs creation, management, and display. 

Sphinx reads files in `reStructuredText <http://sphinx-doc.org/rest.html>`_ and builds a set of HTML pages. Every time a new commit is pushed to github, readthedocs automatically updates documentation. 

Additionally, sphinx knows all about python! The directives ``automodule``, ``autoclass``, ``autofunction`` and more instruct sphinx to inspect the code located in ``src/`` and build documentation from the docstrings within.

For example, the directive ``.. automodule:: paradrop.backend`` will build all the documentation for the given package. See google for more instructions. 

All docstring documentation is rebuilt on every commit (unless there's a bug in the code.) Sphinx does not, however, know about structural changes in code! To alert sphinx of these changes, use the ``autodoc`` feature::

    sphinx-apidoc -f -o docs/api src/paradrop/

This scans packages in the ``src/paradrop`` directory and creates .rst files in ``docs/api``. The root file ``index.rst`` links to ``modules.rst``, connecting the newly generated api code with the main documentation.

To create the documentation locally, run::

    cd docs
    make html
    python -m SimpleHTTPServer 9999

Open your web browser of choice and point it to http://localhost:9999/_build/html/index.html.