# Modified by Sizedalloy33 in 2026
# Originally sourced from Universal Blue (Apache-2.0)

# Allow build scripts to be referenced without being copied into the final image
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files

# Base Image
FROM ghcr.io/ublue-os/bazzite:stable
## Other possible base images include:
# FROM ghcr.io/ublue-os/bazzite:testing
# FROM ghcr.io/ublue-os/aurora:stable
# FROM ghcr.io/ublue-os/bluefin-nvidia-open:stable
#
# ... and so on, here are more base images
# Universal Blue Images: https://github.com/orgs/ublue-os/packages
# Fedora base image: quay.io/fedora/fedora-bootc:44
# CentOS base images: quay.io/centos-bootc/centos-bootc:stream10

### [IM]MUTABLE /opt
## Some bootable images, like Fedora, have /opt symlinked to /var/opt, in order to
## make it mutable/writable for users. However, some packages write files to this directory,
## thus its contents might be wiped out when bootc deploys an image, making it troublesome for
## some packages. Eg, google-chrome, docker-desktop.
##
## Uncomment the following line if one desires to make /opt immutable and be able to be used
## by the package manager.
# RUN rm /opt && mkdir /opt

### MODIFICATIONS
## make modifications desired in your image and install packages by modifying the build.sh script
## the following RUN directive does all the things required to run "build.sh" as recommended.
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build.sh

### LIVE BOOT SUPPORT
## Packages and initramfs support needed for a bootable live/squashfs ISO
## (Titanoboa's build script expects these to already be present).
RUN dnf install -y dracut-live livesys-scripts grub2-efi-x64-cdboot xorriso isomd5sum jq && \
    dnf clean all

RUN sh -c 'kernel=$(kernel-install list --json pretty | jq -r ".[] | select(.has_kernel == true) | .version"); \
    DRACUT_NO_XATTR=1 dracut -v --force --zstd --reproducible --no-hostonly \
    --add "dmsquash-live dmsquash-live-autooverlay" \
    "/usr/lib/modules/${kernel}/initramfs.img" "${kernel}"' && \
    mkdir -p /boot/efi && cp -av /usr/lib/efi/*/*/EFI /boot/efi/

RUN sed -i "s/^livesys_session=.*/livesys_session=kde/" /etc/sysconfig/livesys && \
    systemctl enable livesys.service livesys-late.service

# Titanboa reads this file to configure the live ISO's label and GRUB
# boot menu entry. See https://github.com/ublue-os/titanoboa for the format.
RUN mkdir -p /usr/lib/bootc-image-builder && \
    cat > /usr/lib/bootc-image-builder/iso.yaml << 'YAML'
label: "PulsarOS-Live"
grub2:
    default: 0
    timeout: 10
    entries:
    - name: "PulsarOS Live"
      linux: "/images/pxeboot/vmlinuz quiet rhgb root=live:CDLABEL=PulsarOS-Live enforcing=0 rd.live.image"
      initrd: "/images/pxeboot/initrd.img"
YAML

### LINTING
## Verify final image and contents are correct.
RUN bootc container lint
