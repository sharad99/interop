# AUVSI SUAS Puppet Module: memcached_setup
# Installs and configures memcached for the server.
# ==============================================================================

class auvsi_suas::memcached_setup {
    class { 'memcached':
        package_ensure => 'latest',
        max_memory => 512,
        listen_ip => '127.0.0.1',
        tcp_port => 11211,
        udp_port => 11211,
    }
}
