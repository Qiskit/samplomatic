Installation instructions
=========================

Prerequisites
^^^^^^^^^^^^^

First, create a minimal environment with only Python installed in it. We recommend using `Python virtual environments <https://docs.python.org/3.10/tutorial/venv.html>`__.

.. code:: sh

    python3 -m venv /path/to/virtual/environment

Activate your new environment.

.. code:: sh

    source /path/to/virtual/environment/bin/activate




There are two primary ways to install the packages:

- :ref:`Option 1`
- :ref:`Option 2`

.. _Option 1:

Option 1: Install from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The most straightforward way to install the ``samplomatic`` package is via ``PyPI``.

.. code:: sh

    pip install 'samplomatic'


.. _Option 2:

Option 2: Install from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you plan to develop in the repository or run the notebooks locally, you should install from source.

First, clone the ``samplomatic`` repository.

.. code:: sh

    git clone git@github.com:Qiskit/samplomatic.git

Next, upgrade pip and enter the repository.

.. code:: sh

    pip install --upgrade pip
    cd samplomatic

The next step is to install ``samplomatic`` to the virtual environment. If you plan to run the notebooks and their visualizations, install the
notebook dependencies.
If you plan on developing in the repository, install the ``dev`` and ``vis`` dependencies.

Adjust the options below to suit your needs.

.. code:: sh

    pip install -e ".[dev,vis]"
