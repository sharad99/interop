# AUVSI SUAS Puppet Module: base
# Base, core system setup
# ==============================================================================

# Should be required by anything that needs to install or use packages
class auvsi_suas::base {
    require auvsi_suas::apt_sources

    # Install python and pip
    class { 'python' :
        ensure => 'latest',
        version => 'system',
        pip => 'latest',
        virtualenv => 'latest',
    }

    # Some core programs
    $package_deps = [
        "ntp",
        "openssh-client",
        "openssh-server",
        "rsync",
        "vim",
        "git",
        # The Puppet Python class can't actually handle installing multiple
        # versions of Python, so we handle Python 3 ourselves.
        "python3",
        "python3-pip",
    ]
    package { $package_deps:
        ensure => "latest",
    }

    class { 'nodejs': }
}
