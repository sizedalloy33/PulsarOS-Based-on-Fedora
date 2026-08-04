#!/bin/bash

set -ouex pipefail

# Copy the contents of system_files/ of the git repo to /
cp -avf "/ctx/system_files"/. /

# Ensure execution permissions on custom profile scripts
chmod +x /etc/profile.d/*.sh
chmod +x /usr/bin/pulsaros-welcome-app.py
chmod +x /etc/xdg/autostart/pulsaros-welcome-app.desktop

rm -f /usr/share/applications/bazzite-documentation.desktop

### Install packages

# Packages can be installed from any enabled yum repo on the image.
# RPMfusion repos are available by default in ublue main images
# List of rpmfusion packages can be found here:
# https://mirrors.rpmfusion.org/mirrorlist?path=free/fedora/updates/43/x86_64/repoview/index.html&protocol=https&redirect=1

# remove rpms included in bazzite that don't apply to the os
rpm-ostree override remove bazzite-portal steamdeck-kde-presets-desktop
rpm-ostree override remove openh264 || echo "not present, skipping"

# enabling an already existing repo
dnf5 config-manager setopt fedora-cisco-openh264.enabled=1

# this installs a package from fedora repos
dnf5 install -y tmux gamemode firefox

# Use a COPR Example:
#
# dnf5 -y copr enable ublue-os/staging
# dnf5 -y install package
# Disable COPRs so they don't end up enabled on the final image:
# dnf5 -y copr disable ublue-os/staging

#### Example for enabling a System Unit File

systemctl enable podman.socket
