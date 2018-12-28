from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild
from conanos.build import config_scheme
import os, shutil

class LibniceConan(ConanFile):
    name = "libnice"
    version = "0.1.14"
    description = "Libnice is an implementation of the IETF's Interactive Connectivity Establishment (ICE) standard (RFC 5245)"
    url = "https://github.com/conanos/libnice"
    homepage = "https://nice.freedesktop.org/"
    license = "LGPL-2.1+","MPL-1.1"
    exports = ["COPYING", "shared/*","libnice.def","rand.c","bind.c"]
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    #requires= ("libffi/3.3-rc0@conanos/dev","glib/2.58.0@conanos/dev",
    #"gtk-doc-lite/1.27@conanos/dev","gstreamer-1.0/1.14.4@conanos/dev",
    #"gnutls/3.5.18@conanos/dev","nettle/3.4@conanos/dev",
    #"libtasn1/4.13@conanos/dev","gmp/6.1.2@conanos/dev")

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def requirements(self):
        self.requires.add("glib/2.58.1@conanos/stable")
        self.requires.add("gstreamer/1.14.4@conanos/stable")
        self.requires.add("gnutls/3.5.19@conanos/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_="https://github.com/libnice/libnice/archive/{version}.tar.gz"
        tools.get(url_.format(version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        if self.settings.os == 'Windows':
            sln_folder = "shared" if self.options.shared else "static"
            for f in os.listdir(os.path.join(self.source_folder,sln_folder)):
                shutil.copy2(os.path.join(self.source_folder,sln_folder,f),os.path.join(self.source_folder,self._source_subfolder,"win32","vs9",f))
                self._replace_include_and_dependency(os.path.join(self.source_folder,self._source_subfolder,"win32","vs9",f))
            shutil.copy2(os.path.join(self.source_folder,"rand.c"),os.path.join(self.source_folder,self._source_subfolder,"stun","rand.c"))
            shutil.copy2(os.path.join(self.source_folder,"bind.c"),os.path.join(self.source_folder,self._source_subfolder,"stun","usages","bind.c"))
            shutil.copy2(os.path.join(self.source_folder,"libnice.def"),os.path.join(self.source_folder,self._source_subfolder,"win32","vs9","libnice.def"))

    def _replace_include_and_dependency(self, proj):
        replacements = {
            "..\..\glib\include\glib-2.0":";".join([os.path.join(self.deps_cpp_info["glib"].rootpath,"include\glib-2.0"),
                                                   os.path.join(self.deps_cpp_info["gnutls"].rootpath,"include")]),
            "..\..\glib\lib\glib-2.0\include" : os.path.join(self.deps_cpp_info["glib"].rootpath,"lib\glib-2.0\include"),
            "..\..\glib\lib" : ";".join([os.path.join(self.deps_cpp_info["glib"].rootpath,"lib"),
                                         os.path.join(self.deps_cpp_info["gnutls"].rootpath,"lib")]),
            "gio-2.0.lib" : " ".join(["gio-2.0.lib","gnutls%s.lib"%("d" if self.options.shared else "")]),
            "Name=\"VCCLCompilerTool\"" : "\n".join(["Name=\"VCCLCompilerTool\"","AdditionalOptions=\"/FS\""])
        }
        for s, r in replacements.items():
            tools.replace_in_file(proj,s,r,strict=False)

    def build(self):
        #with tools.chdir(self.source_subfolder):
        #    with tools.environment_append({
        #        'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
        #        ":%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
        #        %(self.deps_cpp_info["libffi"].rootpath,self.deps_cpp_info["glib"].rootpath,
        #        self.deps_cpp_info["gtk-doc-lite"].rootpath,self.deps_cpp_info["gstreamer-1.0"].rootpath,
        #        self.deps_cpp_info["gnutls"].rootpath,self.deps_cpp_info["nettle"].rootpath,
        #        self.deps_cpp_info["libtasn1"].rootpath,),
        #        'LIBRARY_PATH' : '%s/lib'%(self.deps_cpp_info["gmp"].rootpath),
        #        'LD_LIBRARY_PATH' : "%s/lib:%s/lib"%(self.deps_cpp_info["libffi"].rootpath,self.deps_cpp_info["glib"].rootpath)
        #        }):

        #        self.run('autoreconf -f -i')
        #        _args = ["--prefix=%s/builddir"%(os.getcwd()),"--with-gstreamer", "--without-gstreamer-0.10",
        #                 "--enable-compile-warnings=maximum", "--disable-gtk-doc"]
        #        if self.options.shared:
        #            _args.extend(['--enable-shared=yes','--enable-static=no','--enable-static-plugins=no'])
        #        else:
        #            _args.extend(['--enable-shared=no','--enable-static=yes','--enable-static-plugins=yes'])
        #        self.run('./configure %s'%(' '.join(_args)))
        #        self.run('make -j4')
        #        self.run('make install')
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"win32","vs9")):
                msbuild = MSBuild(self)
                msbuild.build("libnice.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'})

    def package(self):
        if self.settings.os == 'Windows':
            platforms = {'x86': 'Win32', 'x86_64': 'x64'}
            output_rpath = os.path.join("win32","vs9",platforms.get(str(self.settings.arch)),str(self.settings.build_type))
            self.copy("libnice.*", dst=os.path.join(self.package_folder,"lib"),
                      src=os.path.join(self.build_folder,self._source_subfolder,output_rpath), excludes=["libnice.dll","libnice.tlog"])
            self.copy("libnice.dll", dst=os.path.join(self.package_folder,"bin"),
                      src=os.path.join(self.build_folder,self._source_subfolder,output_rpath))
            self.copy("*.exe", dst=os.path.join(self.package_folder,"bin"),
                      src=os.path.join(self.build_folder,self._source_subfolder,output_rpath))
            self.copy("nice.h", dst=os.path.join(self.package_folder,"include"),
                      src=os.path.join(self.build_folder,self._source_subfolder,"nice"))
            for i in ["address.h","agent.h","candidate.h","debug.h"]:
                self.copy(i, dst=os.path.join(self.package_folder,"include"),
                          src=os.path.join(self.build_folder,self._source_subfolder,"agent"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            replacements = {
                "@prefix@"          : self.package_folder,
                "@exec_prefix@"     : "${prefix}/lib",
                "@libdir@"          : "${prefix}/lib",
                "@includedir@"      : "${prefix}/include",
                "@UPNP_ENABLED@"    : "",
                "@VERSION@"         : self.version,
                "@NICE_PACKAGES_PUBLIC@"   : "glib-2.0 >= 2.44 gio-2.0 >= 2.44 gobject-2.0 >= 2.44",
                "@GUPNP_PACKAGES_PUBLIC@"  : "",
                "@NICE_PACKAGES_PRIVATE@"  : "gthread-2.0 gnutls >= 2.12.0",
                "@GUPNP_PACKAGES_PRIVATE@" : "",
            }
            shutil.copy(os.path.join(self.build_folder,self._source_subfolder,"nice","nice.pc.in"),
                        os.path.join(self.package_folder,"lib","pkgconfig","nice.pc"))
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig","nice.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

