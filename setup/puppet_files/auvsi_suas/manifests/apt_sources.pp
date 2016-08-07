# AUVSI SUAS Puppet Module: apt_sources
# Enable all standard Ubuntu repos: main restricted universe multiverse
# ==============================================================================

# apt_sources module definition
class auvsi_suas::apt_sources {
    include apt

    apt::source { "ubuntu_xenial":
        location        => "http://archive.ubuntu.com/ubuntu/",
        release         => "xenial",
        repos           => "main restricted universe multiverse",
    }

    apt::source { "ubuntu_xenial-updates":
        location        => "http://archive.ubuntu.com/ubuntu/",
        release         => "xenial-updates",
        repos           => "main restricted universe multiverse",
    }

    apt::source { "ubuntu_xenial-security":
        location        => "http://archive.ubuntu.com/ubuntu/",
        release         => "xenial-security",
        repos           => "main restricted universe multiverse",
    }
}
