Vagrant Setup
=============

Using Vagrant makes setup quite simple.

#. `Install Vagrant <https://www.vagrantup.com/>`__
#. `Install Vagrant Virtualbox Guest Additions`__

.. code-block:: bash

   $ vagrant plugin install vagrant-vbguest

#. `Install Box for
   Ubuntu <https://docs.vagrantup.com/v2/boxes.html>`__. You want the
   box ubuntu/xenial64.
#. `Start
   Vagrant <https://docs.vagrantup.com/v2/getting-started/index.html>`__.

.. code-block:: bash

    $ cd ~/interop/setup
    $ vagrant up

This will create a virtual machine (VM), map the VM ports to the host
ports, and perform the automated system setup (dependencies, database,
Apache, etc.). Once you execute these commands and the machine is setup,
you should be able to access the competition server from within the VM
at http://localhost, or from the host at http://localhost:8000.
