"""
The intention of this file is to support a small preamble that can go into the
first cell of any jupyter notebook that allows users to easily provision the
Colab server with drake iff the notebook is being run on Colab, but which fails
fast when run on a local machine.
"""

import importlib
import os
import shutil
import subprocess
import sys
import warnings
from urllib.request import urlretrieve


def setup_drake(*, version, build='nightly'):
    """Installs drake on Google's Colaboratory and (if necessary) adds the
    installation location to `sys.path`.  This will take approximately two
    minutes, mostly to provision the machine with drake's prerequisites, but
    the server should remain provisioned for 12 hours. Colab may ask you to
    "Reset all runtimes"; say no to save yourself the reinstall.

    Args:
        version: A string to identify which revision of drake to install.
        build: An optional string to specify the hosted directory on
            https://drake-packages.csail.mit.edu/drake/ of the build
            identified by version.  Current options are 'nightly',
            'continuous', or 'experimental'.  Default is 'nightly', which is
            recommended.

    Note: Possible version names vary depending on the build.
        - Nightly builds are versioned by date, e.g., '20200725', and the date
          represents the *morning* (not the prior evening) of the build.  You
          can also use 'latest'.
        - Continuous builds are only available with the version 'latest'.
        - (Advanced) Experimental builds use the version name
          '<timestamp>-<commit>'. See
          https://drake.mit.edu/jenkins#building-binary-packages-on-demand for
          information on obtaining a binary from an experimental branch.

    See https://drake.mit.edu/from_binary.html for more information.

    Note: If you already have pydrake installed to the target location, this
        will overwrite that installation.  If you have pydrake available on
        your ``sys.path`` in a location that is different than the target
        installation, this script will throw an Exception to avoid
        possible confusion.  If you had already imported pydrake, this script
        will throw an assertion to avoid promising that we can succesfully
        reload the module.
    """

    assert 'google.colab' in sys.modules, (
        "This script is intended for use on Google Colab only.")
    assert 'pydrake' not in sys.modules, (
        "You have already imported a version of pydrake.  Please choose "
        "'Restart runtime' from the menu to restart with a clean environment.")

    if os.path.isdir('/opt/drake'):
        shutil.rmtree('/opt/drake')

    # Check for existing pydrake installations.
    spec = importlib.util.find_spec('pydrake')
    if spec is not None:
        raise Exception("Found a conflicting version of pydrake on your "
                        f"sys.path at {spec.origin}.  Please remove it from "
                        "the path to avoid ambiguity.")

    base_url = 'https://drake-packages.csail.mit.edu/drake/'
    urlretrieve(f"{base_url}{build}/drake-{version}-bionic.tar.gz",
                'drake.tar.gz')
    subprocess.run(['tar', '-xzf', 'drake.tar.gz', '-C', '/opt'], check=True)
    subprocess.run(['apt-get', 'update', '-o',
                    'APT::Acquire::Retries=4', '-qq'], check=True)
    with open("/opt/drake/share/drake/setup/packages-bionic.txt",
              "r") as f:
        packages = f.read().splitlines()
    subprocess.run(['apt-get', 'install', '-o',
                    'APT::Acquire::Retries=4', '-o', 'Dpkg::Use-Pty=0', '-qy',
                    '--no-install-recommends'] + packages, check=True)

    # Check if our new installation is already in the path.
    spec = importlib.util.find_spec('pydrake')
    if spec is None:
        v = sys.version_info
        path = f"/opt/drake/lib/python{v.major}.{v.minor}/site-packages"
        sys.path.append(path)
        spec = importlib.util.find_spec('pydrake')

    # Confirm that we now have pydrake on the path.
    assert spec is not None, (
        "Installation failed.  find_spec('pydrake') returned None.")
