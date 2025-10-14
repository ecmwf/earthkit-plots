Development
===========

Contributions
-------------

The code repository is hosted on `Github`_, testing, bug reports and contributions are highly welcomed and appreciated. Feel free to fork it and submit your PRs against the **develop** branch.

Development setup
-----------------------

The recommended development environment is based on **conda**.

First, clone the repository locally. You can use the following command:

.. code-block:: shell

   git clone --branch develop git@github.com:ecmwf/earthkit-plots.git


Next, enter your git repository and run the following commands:

.. code-block:: shell

    make conda-env-update
    conda activate earthkit-plots
    make setup
    pip install -e .

This will create a new conda environment called "earthkit-plots" with all the dependencies installed into it. This setup enables the `pre-commit`_ hooks, performing a series of quality control checks on every commit. If any of these checks fails the commit will be rejected.

Run unit tests
---------------

To run the core test suite, you can use the following command:

.. code-block:: shell

    make unit-tests

In addition to the core unit tests, the test suite also includes image tests. These tests are used to ensure that a set of pre-defined plots have not changed in an unintended way. To run these tests, you can use the following command:

.. code-block:: shell

    make image-tests

If your changes have affected any of the baseline images and you want to update them, you can use the following command:

.. code-block:: shell

    make generate-test-images

You will need to manually upload the generated images to the `earthkit-plots-test-images`_ repository, which will then be used by the CI pipeline to run the image tests against. To do this, you can use the following commands (replace ``<branch-name>`` with the name of the branch you want to create):

.. code-block:: shell

    cd tests/.earthkit-plots-test-images
    git checkout -b <branch-name>
    git add .
    git commit -m "Update baseline images"
    git push

You will then need to create a pull request against the `earthkit-plots-test-images`_ repository with your changes, to be release alongside the new version of earthkit-plots.

Build documentation
-------------------

To build the documentation locally, please install the Python dependencies first:

.. code-block:: shell

    cd docs
    pip install -r requirements.txt
    make html

To see the generated HTML documentation open the ``docs/_build/html/index.html`` file in your browser.


.. _`Github`: https://github.com/ecmwf/earthkit-plots
.. _`pre-commit`: https://pre-commit.com/
