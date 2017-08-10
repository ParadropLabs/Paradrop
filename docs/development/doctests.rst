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

    sphinx-apidoc -f -o docs/api paradrop/paradrop/

This scans packages in the ``src/paradrop`` directory and creates .rst files in ``docs/api``. The root file ``index.rst`` links to ``modules.rst``, connecting the newly generated api code with the main documentation.

To create the documentation locally, run::

    cd docs
    make html
    python -m SimpleHTTPServer 9999

Open your web browser of choice and point it to http://localhost:9999/_build/html/index.html.


Testing
-------

As mentioned above, all testing is automatically run by travis-ci, a continuous integration service. 

To manually run tests, install nosetest::

    pip install nose

Install the required packages::

    pip install -r docs/requirements.txt

Run all tests::

    nosetests

Well thats easy. How does nose detect tests? All tests live in the ``tests/`` directory. Nose adheres to a simple principle: anything marked with ``test`` in its name is most likely a test. When writing tests, make sure all functions begin with ``test``.

Coverage analysis detects how much of the code is used by a test suite. If the result of the coverage is less than 100%, someone slacked. Install coveralls::

    pip install coveralls

Run tests with coverage analysis::

    nosetests --with-coverage --cover-package=paradrop

