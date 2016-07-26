#!/bin/bash

# This script launches the Puppet automated dependency installer.
# ==============================================================================

# Quit immediately on any error
set -e

SETUP=$(readlink -f $(dirname ${BASH_SOURCE[0]}))
REPO=$(readlink -f ${SETUP}/..)
PUPPET=/opt/puppetlabs/bin/puppet

# $1 = log message
function log() {
    local C='\033[0;32m'
    local NC='\033[0m'
    printf "${C}$1${NC}\n"
}

# $1 = module name
function ensure_puppet_module() {
    local module="$1"
    local installed=0

    if ${PUPPET} module list | grep -q ${module}; then
        installed=1
    fi

    if [[ ${installed} == 0 ]]; then
        ${PUPPET} module install ${version_arg} ${module}
    else
        log "Puppet module \"${module}\" already installed"
    fi

    ${PUPPET} module upgrade ${module}
}

# Save all output to a log file.
exec &> >(tee ${SETUP}/setup-$(date +%F-%H-%M-%S).log)

# Create soft link from repo to standardize scripts
log "Creating softlinks..."
ln -snf ${REPO} /interop

# Install puppet repo.
set +e
version=$(dpkg-query --showformat='${Version}' --show puppet-agent)
set -e
if [[ $? != 0 || (( ${version} < 1.4 )) ]]; then
    log "Installing puppetlab repo..."
    wget https://apt.puppetlabs.com/puppetlabs-release-pc1-precise.deb -O /tmp/puppetlabs-release-pc1-precise.deb
    dpkg -i /tmp/puppetlabs-release-pc1-precise.deb
    rm /tmp/puppetlabs-release-pc1-precise.deb
fi

# Update the package list
log "Updating package list..."
apt-get -y update

# Install Puppet
log "Installing Puppet and modules..."
apt-get -y install puppet-agent
mkdir -p /etc/puppet/modules/
ensure_puppet_module puppetlabs-stdlib
ensure_puppet_module puppetlabs-concat
ensure_puppet_module puppetlabs-apt
ensure_puppet_module puppetlabs-postgresql
ensure_puppet_module puppetlabs-apache
ensure_puppet_module puppetlabs-nodejs
ensure_puppet_module stankevich-python
ensure_puppet_module saz-memcached

# Launch the Puppet process. Prepares machine.
log "Executing Puppet setup..."
set +e
${PUPPET} apply \
    --detailed-exitcodes \
    --modulepath=${SETUP}/puppet_files:/etc/puppetlabs/code/environments/production/modules \
    ${SETUP}/puppet_files/auvsi_suas.pp

# Exit codes 0 and 2 indicate success, so rewrite code 2 as 0.
# https://docs.puppet.com/puppet/latest/reference/man/agent.html#OPTIONS
code=$?
if [[ ${code} == 2 ]]; then
    code=0
fi
exit ${code}
