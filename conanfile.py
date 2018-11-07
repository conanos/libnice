from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from shutil import copyfile
import os

class LibniceConan(ConanFile):
    name = "libnice"
    version = "0.1.14"
    description = "Libnice is an implementation of the IETF's Interactive Connectivity Establishment (ICE) standard (RFC 5245)"
    url = "https://github.com/conan-multimedia/libnice"
    homepage = "https://nice.freedesktop.org/wiki/"
    license = "LGPLv2_1Plus"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires= ("libffi/3.3-rc0@conanos/dev","glib/2.58.0@conanos/dev",
    "gtk-doc-lite/1.27@conanos/dev","gstreamer-1.0/1.14.4@conanos/dev",
    "gnutls/3.5.18@conanos/dev","nettle/3.4@conanos/dev",
    "libtasn1/4.13@conanos/dev","gmp/6.1.2@conanos/dev")

    source_subfolder = "source_subfolder"

    def source(self):
        tools.get('http://nice.freedesktop.org/releases/%s-%s.tar.gz'%(self.name, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            with tools.environment_append({
                'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
                ":%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
                %(self.deps_cpp_info["libffi"].rootpath,self.deps_cpp_info["glib"].rootpath,
                self.deps_cpp_info["gtk-doc-lite"].rootpath,self.deps_cpp_info["gstreamer-1.0"].rootpath,
                self.deps_cpp_info["gnutls"].rootpath,self.deps_cpp_info["nettle"].rootpath,
                self.deps_cpp_info["libtasn1"].rootpath,),
                'LIBRARY_PATH' : '%s/lib'%(self.deps_cpp_info["gmp"].rootpath),
                'LD_LIBRARY_PATH' : "%s/lib:%s/lib"%(self.deps_cpp_info["libffi"].rootpath,self.deps_cpp_info["glib"].rootpath)
                }):

                self.run('autoreconf -f -i')
                _args = ["--prefix=%s/builddir"%(os.getcwd()),"--with-gstreamer", "--without-gstreamer-0.10",
                         "--enable-compile-warnings=maximum", "--disable-gtk-doc"]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no','--enable-static-plugins=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes','--enable-static-plugins=yes'])
                self.run('./configure %s'%(' '.join(_args)))
                self.run('make -j4')
                self.run('make install')

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                excludes="*.a" if self.options.shared else  "*.so*"
                self.copy("*", src="%s/builddir"%(os.getcwd()), excludes=excludes)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

