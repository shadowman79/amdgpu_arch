from debian import deb822
import re
import gzip
import lzma
import tarfile
import subprocess
import hashlib
import glob

pkgver_base = "18.50"
pkgver_build = "756341"
pkgrel = 1
debug_pkgext = False


pkgver = "{0}.{1}".format(pkgver_base, pkgver_build)
url_ref="https://www.amd.com/ru/support/kb/release-notes/rn-rad-lin-18-50-unified"
dlagents="https::/usr/bin/wget --referer {0} -N %u".format(url_ref)

            # https://drivers.amd.com/drivers/linux/amdgpu-pro-18.50-756341-ubuntu-18.04.tar.xz
source_url = "https://drivers.amd.com/drivers/linux/amdgpu-pro-{0}-{1}-ubuntu-18.04.tar.xz".format(pkgver_base, pkgver_build)
source_file = "amdgpu-pro-{0}-{1}-ubuntu-18.04.tar.xz".format(pkgver_base, pkgver_build)

def gen_arch_packages():
	arch_packages = {
        
        'amdgpu': Package(
            arch = ['any'],
			desc = "Meta package to install amdgpu userspace components",			
		),        
        
		'amdgpu-pro': Package(
			desc = "Meta package to install amdgpu Pro components",
			arch=['i686', 'x86_64'],
			 depends = ["'libelf'"],
        ),
        
        'amdgpu-pro-core': Package(
            arch = ['any'],
			desc = "Core meta package for unified amdgpu driver.",			
		),
        
        'amdgpu-core': Package(
            arch = ['any'],
            depends = ["'amdgpu-dkms'",""],
            install = "amdgpu-core.install",
			desc = "Core meta package for unified amdgpu driver.",
		),
        
        'amf-amdgpu-pro': Package(
            depends = ["'libgl'"],
			desc = "AMDGPU Pro Advanced Multimedia Framework",			
		),        

		'amdgpu-dkms': Package(
            provides = ['amdgpu=18.50'],
            depends = ["'dkms>=1.95'"],#"'linux=4.16.9'","'linux-headers=4.16.9'"],
			arch = ['any'],
			desc = "The AMDGPU Pro kernel module",
			extra_commands = [
				"msg 'Applying patches...'",
				"(cd ${{pkgdir}}/usr/src/amdgpu-{0}-{1};".format(pkgver_base, pkgver_build),
				"\tsed -i 's/\/extra/\/extramodules/' dkms.conf",
				";\n".join(["\t\tmsg2 '{0}'\n\t\tpatch -p1 -i \"${{srcdir}}/{0}\"".format(patch) for patch in patches]),
				")",
				]
		),

		'opencl-amdgpu': Package(
			desc = "The AMDGPU Pro OpenCL implementation",
			depends = ["'ocl-icd'"],
			provides  = ['opencl-driver'],
            extra_commands = [
			'mkdir -p "${pkgdir}"/usr/lib/',
			'mkdir -p "${pkgdir}"/usr/bin/',
			'ln -s /opt/amdgpu-pro/bin/clinfo "${pkgdir}"/usr/bin/clinfo',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libamdocl64.so "${pkgdir}"/usr/lib/libamdocl64.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libcltrace.so "${pkgdir}"/usr/lib/libcltrace.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libhsakmt.so "${pkgdir}"/usr/lib/libhsakmt.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libhsakmt.so.1 "${pkgdir}"/usr/lib/libhsakmt.so.1',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libhsakmt.so.1.0.0 "${pkgdir}"/usr/lib/libhsakmt.so.1.0.0',
			]
		),
        
        'opencl-orca-amdgpu': Package(
			desc = "non-free AMD OpenCL ICD Loaders",
			depends = ["'gcc-libs'"],
			 extra_commands = [
			'mkdir -p "${pkgdir}"/usr/lib/',			
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libamdocl-orca64.so "${pkgdir}"/usr/lib/libamdocl-orca64.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libamdocl12cl64.so "${pkgdir}"/usr/lib/libamdocl12cl64.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libOpenCL.so "${pkgdir}"/usr/lib/libOpenCL.so',
			'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libOpenCL.so.1 "${pkgdir}"/usr/lib/libOpenCL.so.1',
			]
		),
             
		'libdrm-amdgpu': Package(
			desc = "The AMDGPU Pro userspace interface to kernel DRM services",
			provides = ['libdrm'],
			depends = ["'cunit'"],
			conflicts = ['libdrm'],
			extra_commands = [				
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm.so "${pkgdir}"/usr/lib/libdrm.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm.so.2 "${pkgdir}"/usr/lib/libdrm.so.2',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm.so.2.4.0 "${pkgdir}"/usr/lib/libdrm.so.2.4.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libkms.so "${pkgdir}"/usr/lib/libkms.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libkms.so.1 "${pkgdir}"/usr/lib/libkms.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libkms.so.1.0.0 "${pkgdir}"/usr/lib/libkms.so.1.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_amdgpu.so "${pkgdir}"/usr/lib/libdrm_amdgpu.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_amdgpu.so.1 "${pkgdir}"/usr/lib/libdrm_amdgpu.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_amdgpu.so.1.0.0 "${pkgdir}"/usr/lib/libdrm_amdgpu.so.1.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_radeon.so "${pkgdir}"/usr/lib/libdrm_radeon.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_radeon.so.1 "${pkgdir}"/usr/lib/libdrm_radeon.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libdrm_radeon.so.1.0.1 "${pkgdir}"/usr/lib/libdrm_radeon.so.1.0.1',
            ]
		),
        
 #       'libgbm-amdgpu': Package(
#			desc = "Generic buffer management API ",
#			#depends = ["'mesa-noglvnd-nogbm'"],
#			provides = ['libgbm'],
#			extra_commands = [
#				'mkdir -p "${pkgdir}"/usr/lib/',
#				'mkdir -p "${pkgdir}"/usr/lib/gbm/',
#				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so  "${pkgdir}"/usr/lib/libgbm.so',
#				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so.1  "${pkgdir}"/usr/lib/libgbm.so.1',
#				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so.1.0.0  "${pkgdir}"/usr/lib/libgbm.so.1.0.0',
#				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/gbm/gbm_amdgpu.so  "${pkgdir}"/usr/lib/gbm/gbm_amdgpu.so',
 #           ]
#		),
        
        'llvm-amdgpu': Package(
            provides = ['llvm-libs','llvm'],
            conflicts = ['llvm-libs','llvm'],
            depends = ["'python2'","'ncurses5-compat-libs'","'libedit'"],
			desc = "Generic buffer management API ",
			extra_commands = [
                'mkdir -p "${pkgdir}"/usr/lib/',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/BugpointPasses.so "${pkgdir}"/usr/lib/BugpointPasses.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libLLVM-7.0.1.so "${pkgdir}"/usr/lib/libLLVM-7.0.1.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libLLVM-7.so "${pkgdir}"/usr/lib/libLLVM-7.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libLLVM.so "${pkgdir}"/usr/lib/libLLVM.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libLTO.so "${pkgdir}"/usr/lib/libLTO.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libLTO.so.7 "${pkgdir}"/usr/lib/libLTO.so.7',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/LLVMHello.so "${pkgdir}"/usr/lib/LLVMHello.so',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/TestPlugin.so "${pkgdir}"/usr/lib/TestPlugin.so', 
                'ln -s /usr/lib/libedit.so "${pkgdir}"/usr/lib/libedit.so.2'
             ]
		),

		'vulkan-amdgpu': Package(
			desc = "The AMDGPU Pro Vulkan driver",
			provides = ['vulkan-driver'],
			depends = ["'gcc-libs'"],
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/share/vulkan/icd.d/',
				'mv "${pkgdir}"/opt/amdgpu/etc/vulkan/icd.d/amd_icd64.json "${pkgdir}"/usr/share/vulkan/icd.d/',
				# https://support.amd.com/en-us/kb-articles/Pages/AMDGPU-PRO-Driver-for-Linux-Release-Notes.aspx
				# says you need version 1.0.61 of the vulkan sdk, so I'm guessing this is the correct version supported by this driver
				'sed -i "s@abi_versions\(.*\)0.9.0\(.*\)@api_version\\11.0.61\\2@" "${pkgdir}"/usr/share/vulkan/icd.d/amd_icd64.json',
				'rm -rf "${pkgdir}"/opt/amdgpu/etc/vulkan/'
			]
		),

		'mesa-amdgpu': Package(            
            provides = ['mesa-libgl', 'mesa-dri', 'opengl-driver', 'osmesa', 'mesa'],
            conflicts = ['mesa', 'mesa-vdpau', 'mesa-dri', 'mesa-libgl'],
			desc = "Mesa implementation for AMDGPU Pro. Contains VDPAU video acceleration drivers: these libraries provide the Video Decode and Presentation API for Unix. They provide accelerated video playback (incl. H.264) and video post-processing for the supported graphics cards.",
			#install = mesa-amdgpu.install,
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib/',
				'mkdir -p "${pkgdir}"/usr/lib/dri/',
				'mkdir -p "${pkgdir}"/usr/lib/gbm/',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r300.so.1 "${pkgdir}"/usr/lib/libvdpau_r300.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r300.so.1.0 "${pkgdir}"/usr/lib/libvdpau_r300.so.1.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r300.so.1.0.0 "${pkgdir}"/usr/lib/libvdpau_r300.so.1.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r600.so.1 "${pkgdir}"/usr/lib/libvdpau_r600.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r600.so.1.0 "${pkgdir}"/usr/lib/libvdpau_r600.so.1.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_r600.so.1.0.0 "${pkgdir}"/usr/lib/libvdpau_r600.so.1.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_radeonsi.so.1 "${pkgdir}"/usr/lib/libvdpau_radeonsi.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_radeonsi.so.1.0 "${pkgdir}"/usr/lib/libvdpau_radeonsi.so.1.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/vdpau/libvdpau_radeonsi.so.1.0.0 "${pkgdir}"/usr/lib/libvdpau_radeonsi.so.1.0.0',
				
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/kms_swrast_dri.so "${pkgdir}"/usr/lib/dri/kms_swrast_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/r200_dri.so "${pkgdir}"/usr/lib/dri/r200_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/r300_dri.so "${pkgdir}"/usr/lib/dri/r300_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/r600_dri.so "${pkgdir}"/usr/lib/dri/r600_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/radeon_dri.so "${pkgdir}"/usr/lib/dri/radeon_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/radeonsi_dri.so "${pkgdir}"/usr/lib/dri/radeonsi_dri.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri/swrast_dri.so "${pkgdir}"/usr/lib/dri/swrast_dri.so',
				
           		'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libEGL.so "${pkgdir}"/usr/lib/libEGL.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libEGL.so.1 "${pkgdir}"/usr/lib/libEGL.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libEGL.so.1.0.0 "${pkgdir}"/usr/lib/libEGL.so.1.0.0',
				
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGL.so.1 "${pkgdir}"/usr/lib/libGL.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGL.so.1.2.0 "${pkgdir}"/usr/lib/libGL.so.1.2.0',
				
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libglapi.so.0 "${pkgdir}"/usr/lib/libglapi.so.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libglapi.so.0.0.0 "${pkgdir}"/usr/lib/libglapi.so.0.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGLESv1_CM.so.1 "${pkgdir}"/usr/lib/libGLESv1_CM.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGLESv1_CM.so.1.1.0 "${pkgdir}"/usr/lib/libGLESv1_CM.so.1.1.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGLESv2.so "${pkgdir}"/usr/lib/libGLESv2.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGLESv2.so.2 "${pkgdir}"/usr/lib/libGLESv2.so.2',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libGLESv2.so.2.0.0 "${pkgdir}"/usr/lib/libGLESv2.so.2.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libOSMesa.so "${pkgdir}"/usr/lib/libOSMesa.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libOSMesa.so.8 "${pkgdir}"/usr/lib/libOSMesa.so.8',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libOSMesa.so.8.0.0 "${pkgdir}"/usr/lib/libOSMesa.so.8.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libxatracker.so "${pkgdir}"/usr/lib/libxatracker.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libxatracker.so.2 "${pkgdir}"/usr/lib/libxatracker.so.2',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libxatracker.so.2.4.0 "${pkgdir}"/usr/lib/libxatracker.so.2.4.0',
				
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so  "${pkgdir}"/usr/lib/libgbm.so',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so.1  "${pkgdir}"/usr/lib/libgbm.so.1',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libgbm.so.1.0.0  "${pkgdir}"/usr/lib/libgbm.so.1.0.0',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/gbm/gbm_amdgpu.so  "${pkgdir}"/usr/lib/gbm/gbm_amdgpu.so',				
				
				'ln -s /opt/amdgpu/lib/libomxil-bellagio0/libomx_mesa.so "${pkgdir}"/usr/lib/libomx_mesa.so',
		
				# Support I+A hybrid graphics
				'if [ -f /usr/lib/dri/i965_dri.so ] && [ "/usr/lib/dri" != "/opt/amdgpu/lib/x86_64-linux-gnu/dri" ]; then',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/dri "${pkgdir}"/usr/lib/dri/i965_dri.so',
				'fi',				
			]
		),
            
            
        'amdgpu-libgl': Package(
			desc = "free implementation of the OpenGL API -- GLX development files",			
			provides=['libgl', 'libegl', 'libgles'],
			conflicts=['libgl', 'libegl', 'libgles', 'libglvnd'],
			extra_commands = [
                'mkdir -p "${pkgdir}"/usr/lib/',
                'mkdir -p "${pkgdir}"/usr/lib/dri/',
                'mkdir -p "${pkgdir}"/usr/lib/xorg/modules/extensions/',
                'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libEGL.so "${pkgdir}"/usr/lib/libEGL.so',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libEGL.so.1 "${pkgdir}"/usr/lib/libEGL.so.1',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libGL.so "${pkgdir}"/usr/lib/libGL.so',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libGL.so.1 "${pkgdir}"/usr/lib/libGL.so.1',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libGL.so.1.2 "${pkgdir}"/usr/lib/libGL.so.1.2',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libGLESv2.so "${pkgdir}"/usr/lib/libGLESv2.so',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libGLESv2.so.2 "${pkgdir}"/usr/lib/libGLESv2.so.2',
                'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libglapi.so "${pkgdir}"/usr/lib/libglapi.so',
				'ln -s /opt/amdgpu-pro/lib/x86_64-linux-gnu/libglapi.so.1 "${pkgdir}"/usr/lib/libglapi.so.1',
				'ln -s /opt/amdgpu-pro/lib/xorg/modules/extensions/libglx.so "${pkgdir}"/usr/lib/xorg/modules/extensions/libglx.so',				
				"# This is needed because libglx.so has a hardcoded DRI_DRIVER_PATH",
				"mv \"${pkgdir}\"/usr/lib/x86_64-linux-gnu/dri ${pkgdir}/usr/lib/",
				"ln -s /usr/lib/dri ${pkgdir}/usr/lib/x86_64-linux-gnu/dri",
				'mkdir -p "${pkgdir}/etc/ld.so.conf.d/"',
                'echo "/opt/amdgpu-pro/lib/x86_64-linux-gnu/" > "${pkgdir}"/etc/ld.so.conf.d/amdgpu-pro.conf',				
			]
		),
        
#        'mesa-amdgpu-omx-drivers': Package(
#			desc = "Mesa OpenMAX video drivers for AMDGPU Pro",
#		),
        
		'gst-omx-amdgpu': Package(
			desc = "GStreamer OpenMAX plugins for AMDGPU Pro",
			 extra_commands = [
            'mkdir -p "${pkgdir}"/usr/lib/gstreamer-1.0/',
            'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/gstreamer-1.0/libgstomx.so "${pkgdir}"/usr/lib/gstreamer-1.0/libgstomx.so',
            ]
		),
        
        'wsa-amdgpu': Package(
			desc = "Wayland support for AMD Vulkan driver",
			depends = ["'wayland-amdgpu'"],
			 extra_commands = [
            'mkdir -p "${pkgdir}"/usr/lib/',
            'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libamdgpu_wsa_wayland.so "${pkgdir}"/usr/lib/libamdgpu_wsa_wayland.so',
            ]
		),
        
        'wayland-amdgpu':Package(
            conflicts = ['wayland'],
            provides = ['wayland'],
			desc = "Wayland compositor infrastructure",
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib/',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-client.so "${pkgdir}"/usr/lib/libwayland-client.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-client.so.0 "${pkgdir}"/usr/lib/libwayland-client.so.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-client.so.0.3.0 "${pkgdir}"/usr/lib/libwayland-client.so.0.3.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-cursor.so "${pkgdir}"/usr/lib/libwayland-cursor.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-cursor.so.0 "${pkgdir}"/usr/lib/libwayland-cursor.so.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-cursor.so.0.0.0 "${pkgdir}"/usr/lib/libwayland-cursor.so.0.0.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-egl.so "${pkgdir}"/usr/lib/libwayland-egl.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-egl.so.1 "${pkgdir}"/usr/lib/libwayland-egl.so.1',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-egl.so.1.0.0 "${pkgdir}"/usr/lib/libwayland-egl.so.1.0.0',
                'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-server.so "${pkgdir}"/usr/lib/libwayland-server.so',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-server.so.0 "${pkgdir}"/usr/lib/libwayland-server.so.0',
				'ln -s /opt/amdgpu/lib/x86_64-linux-gnu/libwayland-server.so.0.1.0 "${pkgdir}"/usr/lib/libwayland-server.so.0.1.0',
            ]
		),
        
        'wayland-protocols-amdgpu':Package(
			desc = "wayland compositor protocols",
		),
        
        'xf86-video-amdgpu-pro': Package(
			desc = "The AMDGPU Pro X.org video driver",			
			conflicts = ['xf86-video-amdgpu', 'xorg-server>=1.20.0', 'X-ABI-VIDEODRV_VERSION<23', 'X-ABI-VIDEODRV_VERSION>=24'],			
			provides  = ['xf86-video-amdgpu'], # in case anything depends on that
			groups = ['xorg-drivers'],
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib/xorg/modules/drivers/',
				'ln -s /opt/amdgpu/lib/xorg/modules/drivers/amdgpu_drv.so "${pkgdir}"/usr/lib/xorg/modules/drivers/amdgpu_drv.so',
            ]
		),
        
       'xserver-xorg-amdgpu':Package(       
        desc = "X.Org X server -- graphics acceleration module based on OpenGL. Glamor is a library for accelerating 2D graphics using GL functions. This package contains the X.Org module.",
        # To keep libglamoregl from xorg-xserver
        extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib/xorg/modules/',
				'ln -s /opt/amdgpu/lib/xorg/modules/libglamoregl.so "${pkgdir}"/usr/lib/xorg/modules/libglamoregl.so',
            ]
		),
        

 		'lib32-amdgpu-pro': Package(
            depends = ["'lib32-libdrm'","'lib32-libelf'"],
			desc = "The AMDGPU Pro driver package 32bit",			
		),
		
		'lib32-opencl-amdgpu': Package(
            depends = ["'lib32-gcc-libs'"],
			desc = "The AMDGPU Pro OpenCL implementation",
			provides  = ['lib32-opencl-driver']
		),
		
		'lib32-vulkan-amdgpu': Package(
            depends = ["'lib32-gcc-libs'"],
			desc = "The AMDGPU Pro Vulkan driver 32bit",
			provides = ['lib32-vulkan-driver'],
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/share/vulkan/icd.d/',
				'mv "${pkgdir}"/opt/amdgpu/etc/vulkan/icd.d/amd_icd32.json "${pkgdir}"/usr/share/vulkan/icd.d/',
				# https://support.amd.com/en-us/kb-articles/Pages/AMDGPU-PRO-Driver-for-Linux-Release-Notes.aspx
				# says you need version 1.0.61 of the vulkan sdk, so I'm guessing this is the correct version supported by this driver
				'sed -i "s@abi_versions\(.*\)0.9.0\(.*\)@api_version\\11.0.61\\2@" "${pkgdir}"/usr/share/vulkan/icd.d/amd_icd32.json',
				'rm -rf "${pkgdir}"/opt/amdgpu/etc/vulkan/'
			]
		),
		
		'lib32-libdrm-amdgpu': Package(
			desc = "The AMDGPU Pro userspace interface to kernel DRM services 32 bit",
			conflicts = ['lib32-libdrm'],
			provides = ['lib32-libdrm'],
			extra_commands = [				
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm.so "${pkgdir}"/usr/lib32/libdrm.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm.so.2 "${pkgdir}"/usr/lib32/libdrm.so.2',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm.so.2.4.0 "${pkgdir}"/usr/lib32/libdrm.so.2.4.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libkms.so "${pkgdir}"/usr/lib32/libkms.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libkms.so.1 "${pkgdir}"/usr/lib32/libkms.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libkms.so.1.0.0 "${pkgdir}"/usr/lib32/libkms.so.1.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_amdgpu.so "${pkgdir}"/usr/lib32/libdrm_amdgpu.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_amdgpu.so.1 "${pkgdir}"/usr/lib32/libdrm_amdgpu.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_amdgpu.so.1.0.0 "${pkgdir}"/usr/lib32/libdrm_amdgpu.so.1.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_radeon.so "${pkgdir}"/usr/lib32/libdrm_radeon.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_radeon.so.1 "${pkgdir}"/usr/lib32/libdrm_radeon.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libdrm_radeon.so.1.0.1 "${pkgdir}"/usr/lib32/libdrm_radeon.so.1.0.1',				

            ]
		),
		
		'lib32-mesa-amdgpu': Package(
			desc = "Mesa implementation for AMDGPU Pro. Contains 32 bit libs",            
            provides = ['lib32-mesa-libgl', 'lib32-mesa-dri', 'lib32-opengl-driver', 'osmesa', 'lib32-mesa'],
            conflicts = ['lib32-mesa-dri', 'lib32-mesa-libgl'],
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib32/',
				'mkdir -p "${pkgdir}"/usr/lib32/dri/',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r300.so.1 "${pkgdir}"/usr/lib32/libvdpau_r300.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r300.so.1.0 "${pkgdir}"/usr/lib32/libvdpau_r300.so.1.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r300.so.1.0.0 "${pkgdir}"/usr/lib32/libvdpau_r300.so.1.0.0',				
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r600.so.1 "${pkgdir}"/usr/lib32/libvdpau_r600.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r600.so.1.0 "${pkgdir}"/usr/lib32/libvdpau_r600.so.1.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_r600.so.1.0.0 "${pkgdir}"/usr/lib32/libvdpau_r600.so.1.0.0',				
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_radeonsi.so.1 "${pkgdir}"/usr/lib32/libvdpau_radeonsi.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_radeonsi.so.1.0 "${pkgdir}"/usr/lib32/libvdpau_radeonsi.so.1.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/vdpau/libvdpau_radeonsi.so.1.0.0 "${pkgdir}"/usr/lib32/libvdpau_radeonsi.so.1.0.0',
				
								
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/kms_swrast_dri.so "${pkgdir}"/usr/lib32/dri/kms_swrast_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/r200_dri.so "${pkgdir}"/usr/lib32/dri/r200_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/radeon_dri.so "${pkgdir}"/usr/lib32/dri/radeon_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/r300_dri.so "${pkgdir}"/usr/lib32/dri/r300_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/r600_dri.so "${pkgdir}"/usr/lib32/dri/r600_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/radeonsi_dri.so "${pkgdir}"/usr/lib32/dri/radeonsi_dri.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/dri/swrast_dri.so "${pkgdir}"/usr/lib32/dri/swrast_dri.so',
				
				
    			'ln -s /opt/amdgpu/lib/i386-linux-gnu/libEGL.so.1 "${pkgdir}"/usr/lib32/libEGL.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libEGL.so.1.0.0 "${pkgdir}"/usr/lib32/libEGL.so.1.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGL.so "${pkgdir}"/usr/lib32/libGL.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGL.so.1 "${pkgdir}"/usr/lib32/libGL.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGL.so.1.2.0 "${pkgdir}"/usr/lib32/libGL.so.1.2.0',
						
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libglapi.so.0 "${pkgdir}"/usr/lib32/libglapi.so.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libglapi.so.0.0.0 "${pkgdir}"/usr/lib32/libglapi.so.0.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGLESv1_CM.so.1 "${pkgdir}"/usr/lib32/libGLESv1_CM.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGLESv1_CM.so.1.1.0 "${pkgdir}"/usr/lib32/libGLESv1_CM.so.1.1.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGLESv2.so "${pkgdir}"/usr/lib32/libGLESv2.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGLESv2.so.2 "${pkgdir}"/usr/lib32/libGLESv2.so.2',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libGLESv2.so.2.0.0 "${pkgdir}"/usr/lib32/libGLESv2.so.2.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libOSMesa.so "${pkgdir}"/usr/lib32/libOSMesa.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libOSMesa.so.8 "${pkgdir}"/usr/lib32/libOSMesa.so.8',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libOSMesa.so.8.0.0 "${pkgdir}"/usr/lib32/libOSMesa.so.8.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libxatracker.so "${pkgdir}"/usr/lib32/libxatracker.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libxatracker.so.2 "${pkgdir}"/usr/lib32/libxatracker.so.2',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libxatracker.so.2.4.0 "${pkgdir}"/usr/lib32/libxatracker.so.2.4.0',
				
				'ln -s /opt/amdgpu/lib/libomxil-bellagio0/libomx_mesa.so "${pkgdir}"/usr/lib32/libomx_mesa.so',
				
			]
		),
            
#        'lib32-mesa-amdgpu-omx-drivers': Package(
#            desc = "Mesa OpenMAX video drivers for AMDGPU Pro 32bit",			
#       ),
		
		'lib32-gst-omx-amdgpu': Package(
			desc = "GStreamer OpenMAX plugins for AMDGPU Pro 32bit",
			extra_commands = [
				'rm -f "${pkgdir}"/etc/xdg/gstomx.conf'
			]
		),
            
#        'lib32-libgbm-amdgpu': Package(
#			desc = "Generic buffer management API 32 bit",
#            conflicts = ['lib32-libgbm'],
#            replaces = ['lib32-libgbm'],
#		),
        
        'lib32-amdgpu-libgl': Package(
			desc = "free implementation of the OpenGL API -- GLX development files 32 bit",			
			provides = ['lib32-libgl','lib32-libgles','lib32-libegl'],
			conflicts = ['lib32-libgl','lib32-libgles','lib32-libegl','lib32-libglvnd'],
			extra_commands = [
                'mkdir -p "${pkgdir}"/usr/lib32/',                
                'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libEGL.so "${pkgdir}"/usr/lib32/libEGL.so',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libEGL.so.1 "${pkgdir}"/usr/lib32/libEGL.so.1',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libGL.so "${pkgdir}"/usr/lib32/libGL.so',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libGL.so.1 "${pkgdir}"/usr/lib32/libGL.so.1',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libGLESv2.so "${pkgdir}"/usr/lib32/libGLESv2.so',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libGLESv2.so.2 "${pkgdir}"/usr/lib32/libGLESv2.so.2',
                'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libglapi.so "${pkgdir}"/usr/lib32/libglapi.so',
				'ln -s /opt/amdgpu-pro/lib/i386-linux-gnu/libglapi.so.1 "${pkgdir}"/usr/lib32/libglapi.so.1',				
				"mv \"${pkgdir}\"/usr/lib/i386-linux-gnu/dri ${pkgdir}/usr/lib32/",
				"ln -s /usr/lib32/dri ${pkgdir}/usr/lib/i386-linux-gnu/dri",
			]
		),
        
         'lib32-llvm-amdgpu': Package(
            conflicts = ['lib32-llvm','lib32-llvm-libs'],
            provides = ['lib32-llvm-libs','lib32-llvm'],
            depends = ["'lib32-libedit'","'python2'"],
			desc = "Generic buffer management API 32 bit",
			extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib32/',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/BugpointPasses.so "${pkgdir}"/usr/lib32/BugpointPasses.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libLLVM-7.0.1.so "${pkgdir}"/usr/lib32/libLLVM-7.0.1.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libLLVM-7.so "${pkgdir}"/usr/lib32/libLLVM-7.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libLLVM.so "${pkgdir}"/usr/lib32/libLLVM.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libLTO.so "${pkgdir}"/usr/lib32/libLTO.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libLTO.so.7 "${pkgdir}"/usr/lib32/libLTO.so.7',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/LLVMHello.so "${pkgdir}"/usr/lib32/LLVMHello.so',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/TestPlugin.so "${pkgdir}"/usr/lib32/TestPlugin.so', 
				'ln -s /usr/lib32/libedit.so "${pkgdir}"/usr/lib32/libedit.so.2',
			]
		),
         
         'lib32-opencl-orca-amdgpu':Package(
            depends = ["'lib32-glibc'"],
			desc = "non-free AMD OpenCL ICD Loaders 32 bit",
		),
         
        'lib32-wayland-amdgpu':Package(
            conflicts = ['lib32-wayland'],
			provides = ['lib32-wayland'],            
			desc = "Wayland compositor infrastructure 32 bit",
            extra_commands = [
				'mkdir -p "${pkgdir}"/usr/lib32/',			
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-client.so "${pkgdir}"/usr/lib32/libwayland-client.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-client.so.0 "${pkgdir}"/usr/lib32/libwayland-client.so.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-client.so.0.3.0 "${pkgdir}"/usr/lib32/libwayland-client.so.0.3.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-cursor.so "${pkgdir}"/usr/lib32/libwayland-cursor.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-cursor.so.0 "${pkgdir}"/usr/lib32/libwayland-cursor.so.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-cursor.so.0.0.0 "${pkgdir}"/usr/lib32/libwayland-cursor.so.0.0.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-egl.so "${pkgdir}"/usr/lib32/libwayland-egl.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-egl.so.1 "${pkgdir}"/usr/lib32/libwayland-egl.so.1',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-egl.so.1.0.0 "${pkgdir}"/usr/lib32/libwayland-egl.so.1.0.0',
                'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-server.so "${pkgdir}"/usr/lib32/libwayland-server.so',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-server.so.0 "${pkgdir}"/usr/lib32/libwayland-server.so.0',
				'ln -s /opt/amdgpu/lib/i386-linux-gnu/libwayland-server.so.0.1.0 "${pkgdir}"/usr/lib32/libwayland-server.so.0.1.0',
            ]
			
		),
        
        'lib32-wsa-amdgpu':Package(
			desc = "Wayland support for AMD Vulkan driver 32 bit",
            depends = ["'lib32-wayland'"],
		),
        
        'lib32-xserver-xorg-amdgpu-video-amdgpu':Package(
			desc = "X.Org X server -- AMD/ATI Radeon display driver",
		),

	}
	for key in arch_packages:
		arch_packages[key].name = key
	return arch_packages


# this maps which deb packages should go into specific arch package
# packages without mapping go into 'amdgpu-pro'
packages_map_default = 'amdgpu-pro'
packages_map = {
    
    'amdgpu-lib':                       'amdgpu',
    'amdgpu-lib32':                     'amdgpu',
    
    # amdgpu-pro 
    
	'amdgpu':                           'amdgpu-pro',        # deb is metapackage
	'amdgpu-pro':                       'amdgpu-pro',
    'amdgpu-pro-pin':                   'amdgpu-pro',
  
	# amdgpu-core 
	
	'amdgpu-core':                   'amdgpu-core',        # deb is metapackage
    'amdgpu-pro-core':               'amdgpu-pro-core', 
	
	
	'amf-amdgpu-pro':                 'amf-amdgpu-pro',
	
	# libgbm-amdgpu
	
    'libgbm1-amdgpu-pro':               'mesa-amdgpu',
	'libgbm1-amdgpu-pro-base':          'mesa-amdgpu',
    'libgbm1-amdgpu-pro-dev':           'mesa-amdgpu',
     
     
     # llvm-amdgpu
     
 	'llvm-amdgpu-7.0-dev':          'llvm-amdgpu',
	'llvm-amdgpu-7.0':              'llvm-amdgpu',
	'llvm-amdgpu-7.0-runtime':      'llvm-amdgpu',
	'llvm-amdgpu-runtime':          'llvm-amdgpu',
	'llvm-amdgpu-dev':              'llvm-amdgpu',
	'llvm-amdgpu-7.0-doc':          'llvm-amdgpu', 
	'llvm-amdgpu':                  'llvm-amdgpu',
	'libllvm7.0-amdgpu':            'llvm-amdgpu',
 
     # amdgpu-dkms 
     
	'amdgpu-dkms':                  'amdgpu-dkms',
    
    # libdrm-amdgpu-common
    'libdrm-amdgpu-common':         'libdrm-amdgpu',
    
    
	# mesa-amdgpu
		
    'libegl1-amdgpu-mesa':               'mesa-amdgpu',
	'libegl1-amdgpu-mesa-drivers':       'mesa-amdgpu',
	'libegl1-amdgpu-mesa-dev':           'mesa-amdgpu',
	'libgdm-amdgpu-dev':                 'mesa-amdgpu',	
	'libgles1-amdgpu-mesa':              'mesa-amdgpu',
	'mesa-amdgpu-omx-drivers':           'mesa-amdgpu',
	'mesa-amdgpu-common-dev':            'mesa-amdgpu',
    'mesa-amdgpu-va-drivers':            'mesa-amdgpu',
    'mesa-amdgpu-vdpau-drivers':         'mesa-amdgpu',
    'libglapi-amdgpu-mesa':              'mesa-amdgpu',
    'libosmesa6-amdgpu':                 'mesa-amdgpu',
    'libosmesa6-amdgpu-dev':             'mesa-amdgpu',
    'libgl1-amdgpu-mesa-glx':            'mesa-amdgpu',
	'libgl1-amdgpu-mesa-dri':            'mesa-amdgpu',
	'libgl1-amdgpu-mesa-dev':            'mesa-amdgpu',
	'libgles1-amdgpu-mesa-dev':          'mesa-amdgpu',
    'libgles2-amdgpu-mesa':              'mesa-amdgpu',
    'libgles2-amdgpu-mesa-dev':          'mesa-amdgpu',
    'libxatracker2-amdgpu':              'mesa-amdgpu',
    'libxatracker-amdgpu-dev':           'mesa-amdgpu',
	'libgbm1-amdgpu':                    'mesa-amdgpu',
	'libgbm-amdgpu-dev':                 'mesa-amdgpu',  

	'libdrm-amdgpu-amdgpu1':        'libdrm-amdgpu',
	'libdrm-amdgpu-dev':            'libdrm-amdgpu',
	'libdrm-amdgpu-radeon1':        'libdrm-amdgpu',
	'libdrm-amdgpu-utils':          'libdrm-amdgpu',
	'libdrm2-amdgpu':               'libdrm-amdgpu',
	

   	'gst-omx-amdgpu':               'gst-omx-amdgpu',
 	
     # amdgpu-libgl
    
    'libegl1-amdgpu-pro':               'amdgpu-libgl',
    'libgl1-amdgpu-pro-dri':            'amdgpu-libgl',
    'libgles2-amdgpu-pro':              'amdgpu-libgl',
    'libglapi1-amdgpu-pro':             'amdgpu-libgl',   
	'libgl1-amdgpu-pro-ext':            'amdgpu-libgl', 
	'libgl1-amdgpu-pro-glx':            'amdgpu-libgl', 
    'libgl1-amdgpu-pro-appprofiles':    'amdgpu-libgl',
	
    ## contents of this should probably go into /usr/lib/xorg/modules/dri/ instead of /usr/lib/dri ?

    'xserver-xorg-amdgpu-video-amdgpu':   'xf86-video-amdgpu-pro',
	'glamor-amdgpu':                      'xserver-xorg-amdgpu',
    'glamor-amdgpu-dev':                  'xserver-xorg-amdgpu',
      
    
    # opencl-amdgpu
        
	'clinfo-amdgpu-pro':                'opencl-amdgpu',
	'libopencl1-amdgpu-pro':            'opencl-orca-amdgpu',
	'opencl-amdgpu-pro':                'opencl-amdgpu',
	'opencl-amdgpu-pro-dev':            'opencl-amdgpu',
	'opencl-amdgpu-pro-icd':            'opencl-amdgpu',
	'opencl-orca-amdgpu-pro-icd':       'opencl-orca-amdgpu',
	'roct-amdgpu-pro':                  'opencl-amdgpu',
	'roct-amdgpu-pro-dev':              'opencl-amdgpu',
     
    
    
    # vulkan-amdgpu
    'vulkan-amdgpu':                 'vulkan-amdgpu', 
	'vulkan-amdgpu-pro':             'vulkan-amdgpu', 
    
    # wsa-amdgpu
    
    'wsa-amdgpu':                    'wsa-amdgpu',
    
    # wayland-amdgpu
    	
	'libwayland-amdgpu-client0':          'wayland-amdgpu',
	'libwayland-amdgpu-server0':          'wayland-amdgpu',
    'libwayland-amdgpu-cursor0':      'wayland-amdgpu',
    'libwayland-amdgpu-dev':          'wayland-amdgpu',
    'libwayland-amdgpu-doc':          'wayland-amdgpu',
    'libwayland-amdgpu-egl1':         'wayland-amdgpu',
    
    
     'wayland-protocols-amdgpu':       'wayland-protocols-amdgpu',

      
     # 32 bit libs
     
     'lib32-amdgpu':                    'lib32-amdgpu-pro',
     'lib32-amdgpu-pro':                'lib32-amdgpu-pro', # deb is a metapackage
     
     'lib32-amdgpu-lib':                 'lib32-amdgpu-pro', # deb is a metapackage
     'lib32-clinfo-amdgpu-pro':           None,
     'lib32-glamor-amdgpu':               None,
	 'lib32-glamor-amdgpu-dev':           None,
     'lib32-gst-omx-amdgpu':             'lib32-gst-omx-amdgpu',
     'lib32-libdrm-amdgpu-amdgpu1':      'lib32-libdrm-amdgpu',
     'lib32-libdrm-amdgpu-dev':          'lib32-libdrm-amdgpu',
     'lib32-libdrm-amdgpu-radeon1':      'lib32-libdrm-amdgpu',
     'lib32-libdrm-amdgpu-utils':         None,
     'lib32-libdrm2-amdgpu':              'lib32-libdrm-amdgpu',
     
     'lib32-libegl1-amdgpu-mesa':         'lib32-mesa-amdgpu',
     'lib32-libegl1-amdgpu-mesa-dev':      None,
     'lib32-libegl1-amdgpu-mesa-drivers':  'lib32-mesa-amdgpu',
     
     'lib32-libegl1-amdgpu-pro':         'lib32-amdgpu-libgl',
     'lib32-libgbm-amdgpu-dev':          'lib32-mesa-amdgpu',
     'lib32-libgbm1-amdgpu':             'lib32-mesa-amdgpu',
     'lib32-libgbm1-amdgpu-pro':         'lib32-mesa-amdgpu',
	 'lib32-libgbm1-amdgpu-pro-dev':     'lib32-mesa-amdgpu',
     
    'lib32-libgl1-amdgpu-mesa-dev':      'lib32-mesa-amdgpu',
	'lib32-libgl1-amdgpu-mesa-dri':      'lib32-mesa-amdgpu',
	'lib32-libgl1-amdgpu-mesa-glx':      'lib32-mesa-amdgpu',
	'lib32-libgl1-amdgpu-pro-dri':       'lib32-amdgpu-libgl',
	'lib32-libgl1-amdgpu-pro-ext':       'lib32-amdgpu-libgl',
	'lib32-libgl1-amdgpu-pro-glx':       'lib32-amdgpu-libgl',
	
	'lib32-libglapi-amdgpu-mesa':         'lib32-mesa-amdgpu',
	'lib32-libglapi1-amdgpu-pro':         'lib32-amdgpu-libgl',
	'lib32-libgl1-amdgpu-pro-appprofiles':  'lib32-amdgpu-libgl',
    'lib32-libgles1-amdgpu-mesa':         'lib32-mesa-amdgpu',
	'lib32-libgles1-amdgpu-mesa-dev':     'lib32-mesa-amdgpu',
     
     'lib32-libgles2-amdgpu-mesa':        'lib32-mesa-amdgpu',
     'lib32-libgles2-amdgpu-mesa-dev':    'lib32-mesa-amdgpu',     
	 'lib32-libgles2-amdgpu-pro':         'lib32-amdgpu-libgl',
     
        
     # lib32-llvm-amdgpu
     
 	'lib32-llvm-amdgpu-7.0-dev':          'lib32-llvm-amdgpu',
	'lib32-llvm-amdgpu-7.0':              'lib32-llvm-amdgpu',
	'lib32-llvm-amdgpu-7.0-runtime':      'lib32-llvm-amdgpu',
	'lib32-llvm-amdgpu-runtime':          'lib32-llvm-amdgpu',
	'lib32-llvm-amdgpu-dev':              'lib32-llvm-amdgpu',
	'lib32-llvm-amdgpu':                  'lib32-llvm-amdgpu',
	'lib32-libllvm7.0-amdgpu':            'lib32-llvm-amdgpu',
	
    'lib32-libopencl1-amdgpu-pro':        'lib32-opencl-orca-amdgpu',
   
   	'lib32-libosmesa6-amdgpu':                  'lib32-mesa-amdgpu',
    'lib32-libosmesa6-amdgpu-dev':              'lib32-mesa-amdgpu',
   
	'lib32-libwayland-amdgpu-client0':          'lib32-wayland-amdgpu',
	'lib32-libwayland-amdgpu-server0':          'lib32-wayland-amdgpu',
    'lib32-libwayland-amdgpu-cursor0':          'lib32-wayland-amdgpu',
    'lib32-libwayland-amdgpu-dev':              'lib32-wayland-amdgpu',
    'lib32-libwayland-amdgpu-egl1':             'lib32-wayland-amdgpu',
    
    'lib32-libxatracker2-amdgpu':              'lib32-mesa-amdgpu',
    'lib32-libxatracker-amdgpu-dev':           'lib32-mesa-amdgpu',
   
    'lib32-mesa-amdgpu-omx-drivers':           'lib32-mesa-amdgpu',
	'lib32-mesa-amdgpu-common-dev':            'lib32-mesa-amdgpu',
    'lib32-mesa-amdgpu-va-drivers':             'lib32-mesa-amdgpu',
    'lib32-mesa-amdgpu-vdpau-drivers':         'lib32-mesa-amdgpu',
    
    'lib32-opencl-orca-amdgpu-pro-icd':       'lib32-opencl-amdgpu',
    
    
    # lib32-vulkan-amdgpu
    
    'lib32-vulkan-amdgpu':                     'lib32-vulkan-amdgpu', 
	'lib32-vulkan-amdgpu-pro':                 'lib32-vulkan-amdgpu', 
    
    # lib32-wsa-amdgpu
    
    'lib32-wsa-amdgpu':                    'lib32-wsa-amdgpu',
    
    
	# the following are not needed and should be discarded:
	'lib32-xserver-xorg-amdgpu-video-amdgpu':              None,
	
}



## maps debian dependencies to arch dependencies
replace_deps = {
	"libc6":                None,
	"libgcc1":              None,
	"libstdc++6":           None,
	"libexpat1":             "expat",
	"libx11-6":             "libx11",
	"libx11-xcb1":          None,
	"libxcb-xfixes0":        "libxcb",
	"libxcb-dri2-0":        "libxcb",
	"libxcb-dri3-0":        "libxcb",
	"libxcb-present0":      "libxcb",
	"libxcb-sync1":         "libxcb",
	"libxcb-glx0":          "libxcb",
	"libxcb1":              "libxcb",
	"libxext6":             "libxext",
	"libxshmfence1":        "libxshmfence",
	"libxdamage1":          "libxdamage",
	"libxfixes3":           "libxfixes",
	"libxxf86vm1":          "libxxf86vm",
	"libudev1":             "systemd-libs",
	"libudev-dev":          "systemd-libs",  
	"libpciaccess0":        "libpciaccess",
	"libepoxy0":            "libepoxy",
	"libelf1":              None, # no lib32- package in Arch, just disabling for now
	"xserver-xorg-core":    "xorg-server",
	"libcunit1":            "bcunit",
	"libdrm-radeon1":       "libdrm",
	"amdgpu-pro-firmware":  "linux-firmware",
	"libssl1.0.0":          "openssl",
	"zlib1g":               "zlib",

	"libvdpau1": "libvdpau",
	"libvdpau1-amdgpu": "libvdpau",
	"libtinfo5": "ncurses5-compat-libs",
	"libgstreamer1.0-0": "gstreamer",
	"libgstreamer-plugins-base1.0-0": "gst-plugins-base",
	"libglib2.0-0": "glib2",
	"libomxil-bellagio0": "libomxil-bellagio",

	# replace *-dev packages with arch linux ones containing the headers
	"libffi-dev": "libffi",
	"lib32-libffi-dev": "lib32-libffi",
	"libtinfo-dev": "ncurses",
	"lib32-libtinfo-dev": "lib32-ncurses",
	"libedit2": "libedit",
	"libpci3": "pciutils",


	#"libjs-jquery": "jquery",
	#"libjs-underscorea": "underscorejs" # the underscroejs AUR pkg dos not install to /usr/share/javascript !
	"libjs-underscore":    None,
	"libjs-jquery":       None,
	"libjs-underscorea":  None,
	"libnuma1":           "numactl",
	"libxcb-dri2-0-dev":   "libxcb",
	"libxcb-dri3-dev":     "libxcb",
	"libxcb-glx0-dev":     "libxcb",
	"libxcb-sync-dev":     "libxcb",
	"libxcb-present-dev":  "libxcb",
	"libxext-dev":         "libxext",
	"libxfixes-dev":       "libxfixes",
	"libxdamage-dev":      "libxdamage",
	"libxfixes-dev":       "libxfixes",
    "libxshmfence-dev":    "libxshmfence",
    "libxxf86vm-dev":      "libxxf86vm",
    "libx11-dev":          "libx11",
    "libx11-xcb-dev":      "libx11",
    "libffi6":             "libffi",
    "libsystemd":          "systemd-libs",
    "libselinux1":         "libselinux",
    "x11proto-dri2-dev":   "xorgproto",
    "x11proto-gl-dev":     "xorgproto",
    "libmirclient-dev":    None, #mir
    "libva1":               "libva1",
    "libva1-amdgpu":        "libva1",
    "libva2-amdgpu":        "libva",  
    "libva2":               "libva",
    "lib32-libselinux":      None,
    "lib32-systemd-libs":   "lib32-systemd",
    "lib32-xorgproto":      "xorgproto",    
}

## do not convert the dependencies listed to lib32 variants
no_lib32_convert = [
	"binfmt-support",
	"libselinux",
	"systemd-libs",
	"xorgproto"
]

## override the version requirement extracted from deb
replace_version = {
	"linux-firmware": "",
}

## maps debians archs to arch's archs
arch_map = {
	"amd64": "x86_64",
	"i386": "i686",
	"all": "any"
}



subprocess.run(["wget", "--referer", url_ref, "-N", source_url])

def hashFile(file):
	block = 64 * 1024
	hash = hashlib.sha256()
	with open(file, 'rb') as f:
		buf = f.read(block)
		while len(buf) > 0:
			hash.update(buf)
			buf = f.read(block)
	return hash.hexdigest()

sources = [ source_url ]
sha256sums = [ hashFile(source_file) ]

patches = sorted(glob.glob("*.patch"))

for patch in patches:
    sources.append(patch)
    sha256sums.append(hashFile(patch))

#sources.append("20-amdgpu.conf")
#sha256sums.append(hashFile("20-amdgpu.conf"))

header_tpl = """# Author: Janusz Lewandowski <lew21@xtreeme.org>
# Maintainer: David McFarland <corngood@gmail.com>
# Autogenerated from AMD's Packages file

pkgbase=amdgpu-pro-installer
pkgname={package_names}
pkgver={pkgver}
pkgrel={pkgrel}
arch=('x86_64')
url='http://www.amd.com'
license=('custom:AMD')
makedepends=('wget')

DLAGENTS='{dlagents}'

source=({source})
sha256sums=({sha256sums})

"""

if debug_pkgext:
	header_tpl += "PKGEXT=\".pkg.tar\"\n"
	
	
package_functions = """
# extracts a debian package
# $1: deb file to extract
extract_deb() {
	local tmpdir="$(basename "${1%.deb}")"
	rm -Rf "$tmpdir"
	mkdir "$tmpdir"
	cd "$tmpdir"
	ar x "$1"
	tar -C "${pkgdir}" -xf data.tar.xz
}
# move ubuntu specific /usr/lib/x86_64-linux-gnu to /usr/lib
# $1: library dir
# $2: destination (optional)
move_libdir() {
	local libdir="usr/lib"
	if [ -n "$2" ]; then
		libdir="$2"
	fi
	if [ -d "$1" ]; then
		if [ -d "${pkgdir}/${libdir}" ]; then
			cp -ar -t "${pkgdir}/${libdir}/" "$1"/*
			rm -rf "$1"
		else
			mkdir -p "${pkgdir}/${libdir}"
			mv -t "${pkgdir}/${libdir}/" "$1"/*
			rmdir "$1"
		fi
	fi
}
"""

package_header_tpl = """
package_{NAME} () {{
	pkgdesc={DESC}
"""

package_deb_extract_tpl = """	extract_deb "${{srcdir}}"/amdgpu-pro-%s-%s-ubuntu-18.04/{Filename}
""" %(pkgver_base,pkgver_build)

#package_header_i386 = """	move_libdir "${pkgdir}/opt/amdgpu-pro" "usr"
#	move_libdir "${pkgdir}/opt/amdgpu-pro/lib/i386-linux-gnu" "usr/lib32"
package_header_i386 = """
	move_libdir "${pkgdir}/lib" "usr/lib32"
"""

#package_header_x86_64 = """	move_libdir "${pkgdir}/opt/amdgpu-pro" "usr"
#	move_libdir "${pkgdir}/opt/amdgpu-pro/lib/x86_64-linux-gnu"
package_header_x86_64 = """
	move_libdir "${pkgdir}/lib"
"""

package_lib32_cleanup = """

	# lib32 cleanup
	rm -rf "${pkgdir}"/usr/{bin,lib,include,share} "${pkgdir}/var" "${pkgdir}"/opt/amdgpu-pro/{bin,include,share}
	rm -rf "${pkgdir}"/opt/amdgpu-pro/lib/xorg/modules/extensions/
"""

package_footer = """
}
"""

default_arch = ['x86_64']


def quote(string):
	return "\"" + string.replace("\\", "\\\\").replace("\"", "\\\"") + "\""

class Package:
	def __init__(self, **kwargs):
		for arg in kwargs:
			setattr(self, arg, kwargs[arg])

		if not hasattr(self, "arch"):
			self.arch = default_arch
		self.deb_source_infos = []

	def add_deb(self, info):
		self.deb_source_infos.append(info)

		try:
			self.arch = [ arch_map[info["Architecture"]], ]
		except:
			self.arch = default_arch

		if info["Architecture"] == "i386":
			if self.name.startswith('lib32-'):
				self.arch = ['x86_64']
			else:
				import sys
				sys.stderr.write("ERROR: There is a bug in this script, package '%s' is i386 (came from %s) and should start with 'lib32'. Check packages_map!\n" % (self.name,info["Package"]))


		try:
			deps = info["Depends"].split(', ')
		except:
			deps = None

		domap = True
		if self.name == "amdgpu" or self.name == "lib32-amdgpu":
			domap = False

		if deps:
			deps = [ dependencyRE.match(dep).groups() for dep in deps ]
			deps = [(replace_deps[name] if name in replace_deps else name, version) for name, version in deps]
			deps = ["'" + convertName(fix_32(name), info, domap) + convertVersionSpecifier(fix_32(name), version) + "'" for name, version in deps if name]
			deps = [ dep for dep in deps if not dep.startswith("'=")]

			# remove all dependencies on itself
			deps = [ dep for dep in deps if dep[1:len(self.name)+1] != self.name ]

			if hasattr(self, 'depends') and self.depends:
				deps += self.depends

			self.depends = list(sorted(set( deps ))) # remove duplicates and append to already existing dependencies

			if not hasattr(self, 'desc'):
				desc = info["Description"].split("\n")
				if len(desc) > 2:
					desc = desc[0]
				else:
					desc = " ".join(x.strip() for x in desc)

				if info["Architecture"] == "i386":
					desc += ' (32bit libraries)'

				self.desc = desc

	def toPKGBUILD(self):
		ret = package_header_tpl.format(
			NAME=self.name,
			DESC=quote(self.desc) if hasattr(self, 'desc') else quote("No description for package %s" % self.name),
		)

		if hasattr(self, 'install'):
			ret += "	install=%s\n" % self.install

		# add any given list/array with one of those names to the pkgbuild
		for array in ('arch', 'provides', 'conflicts', 'replaces', 'groups', 'optdepends'):
			if(hasattr(self, array)):
				ret += "	%s=('%s')\n" % (array, "' '".join(getattr(self, array)))

		if hasattr(self, 'depends'):
			ret += "	depends=(%s)\n\n" % " ".join(self.depends)

		for info in self.deb_source_infos:
			ret += package_deb_extract_tpl.format(**info)

		if self.name.startswith('lib32-'):
			ret += package_header_i386
		else:
			ret += package_header_x86_64

		if hasattr(self, 'extra_commands'):
			ret += "\n\t# extra_commands:\n\t"
			ret += "\n\t".join( self.extra_commands )

		if self.name.startswith('lib32-'):
			ret += package_lib32_cleanup
		ret += package_footer
		return ret


arch_packages = gen_arch_packages()


# regex for parsing version information of a deb dependency
dependencyRE = re.compile(r"([^ ]+)(?: \((.+)\))?")

deb_archs={}

def convertName(name, info, domap=True):
	ret = name
	if info["Architecture"] == "i386" and (name not in deb_archs or "any" not in deb_archs[name]):
		if not name in no_lib32_convert:
			ret = "lib32-" + name

	if name in packages_map:
		if domap:
			return packages_map[name]
		return ""
	return ret

def convertVersionSpecifier(name, spec):
	if name in replace_version:
		return replace_version[name]
	if name in deb_package_names:
		return "=" + pkgver + "-" + str(pkgrel)
	if not spec:
		return ""

	sign, spec = spec.split(" ", 1)

	spec = spec.strip()
	if ":" in spec:
		whatever, spec = spec.rsplit(":", 1)
	return sign + spec

dep32RE = re.compile(r"(.*):i386")
def fix_32(dep):
	rdep = dep
	match = dep32RE.match(dep)
	if match:
		rdep = match.group(1)
		if not rdep in no_lib32_convert:
			rdep = 'lib32-%s' % rdep
	return rdep


def writePackages(f):
	global deb_package_names
	package_list=[]

	for info in deb822.Packages.iter_paragraphs(f):
		if not info["Package"] in deb_archs:
			deb_archs[info["Package"]] = set()

		deb_archs[info["Package"]].add(info["Architecture"])
		package_list.append(info)

	deb_package_names = ["lib32-" + info["Package"] if info["Architecture"] == "i386" else info["Package"] for info in package_list]

	f.seek(0)

	for info in package_list:
		name = info["Package"]
		arch_pkg = arch_packages[ packages_map_default ]
		if info["Architecture"] == "i386":
			name = "lib32-" + info["Package"]
			arch_pkg = arch_packages[ "lib32-" + packages_map_default ] # use lib32-<default-pkg> for 32bit packages as default package
		if name in packages_map:
			if packages_map[name] in arch_packages:
				arch_pkg = arch_packages[ packages_map[name] ]
			else:
				import sys 
				sys.stderr.write("not found in map = '%s'\n" % name)
				arch_pkg = None				

		if arch_pkg:
			arch_pkg.add_deb(info)

	#	print(convertPackage(info, package_names + optional_names))


# get list of unique arch packages from package map
arch_package_names=list(arch_packages.keys())
arch_package_names.sort()
deb_package_names=[]

print(header_tpl.format(
	package_names="(" + " ".join( arch_package_names ) + ")",
	pkgver=pkgver,
	pkgrel=pkgrel,
	dlagents=dlagents,
	source="\n\t".join(sources),
	sha256sums="\n\t".join(sha256sums)
))

print(package_functions)


with lzma.open(source_file, "r") as tar:
	with tarfile.open(fileobj=tar) as tf:
		with tf.extractfile("amdgpu-pro-%s-%s-ubuntu-18.04/Packages" %(pkgver_base,pkgver_build)) as packages:
			writePackages(packages)

for pkg in arch_package_names:
	print( arch_packages[pkg].toPKGBUILD() )


# Process packages.txt to get the list of source and version packages
source_pkgs = list()
version_pkgs = list()

with open("packages.txt") as f:    
    for line in f:
        if line[0] != '#':
            toks = line.split()
            if len(toks) > 1:
                source_pkgs.append(toks[0])
                version_pkgs.append(toks[1])
                
# Download deps
for index, value in  enumerate(source_pkgs, start=0):
    sources_url = "https://archive.archlinux.org/packages/%s/%s/%s-%s-x86_64.pkg.tar.xz" % (value[0], value, value, version_pkgs[index])
    subprocess.run(["wget", "--referer", url_ref, "-N", sources_url])



