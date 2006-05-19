import sys,os
import glob
from distutils.core import Extension, setup
import distutils.sysconfig
global PYMCA_INSTALL_DIR
global PYMCA_SCRIPTS_DIR

for line in file(os.path.join('PyMca', 'PyMca.py')).readlines():
    if line[:11] == '__version__':
        exec(line)
        # Append cvs tag if working from cvs tree
        if os.path.isdir('.svn') and os.path.isfile(os.sep.join(['.svn', 'entries'])):
            import re
            revision = 0
            revre = re.compile('committed-rev="(\d+)"')
            for match in revre.finditer(open(os.sep.join(['.svn', 'entries'])).read()):
                revision = max(revision, int(match.group(1)))
            __version__ += 'dev_r%i' % revision
        break

# Specify all the required PyMca data
data_files = [('PyMca', ['PyMca/Scofield1973.dict', 'PyMca/McaTheory.cfg']),
              ('PyMca/attdata', glob.glob('PyMca/attdata/*')),
              ('PyMca/HTML', glob.glob('PyMca/HTML/*.*')),
              ('PyMca/HTML/IMAGES', glob.glob('PyMca/HTML/IMAGES/*')),
              ('PyMca/HTML/PyMCA_files', glob.glob('PyMca/HTML/PyMCA_files/*'))]

# The following is not supported by python-2.3:
#package_data = {'PyMca': ['attdata/*', 'HTML/*.*', 'HTML/IMAGES/*', 'HTML/PyMCA_files/*']}
packages = ['PyMca']

sources = glob.glob('*.c')
if sys.platform == "win32":
    define_macros = [('WIN32',None)]
    script_files = []
else:
    define_macros = []
    script_files = glob.glob('PyMca/scripts/*')

def build_FastEdf(ext_modules):
    module  = Extension(name = 'PyMca.FastEdf',
                                            sources = glob.glob('PyMca/edf/*.c'),
                                            define_macros = define_macros)
    ext_modules.append(module)

def build_specfile(ext_modules):
    module  = Extension(name = 'PyMca.specfile',
                                            sources = glob.glob('PyMca/specfile/src/*.c'),
                                            define_macros = define_macros,
                                            include_dirs = ['PyMca/specfile/include'])
    ext_modules.append(module)

def build_specfit(ext_modules):
    module  = Extension(name = 'PyMca.SpecfitFuns',
                                            sources = glob.glob('PyMca/specfit/*.c'),
                                            define_macros = define_macros,
                                            include_dirs = ['PyMca/specfit'])
    ext_modules.append(module)

def build_sps(ext_modules):
    module  = Extension(name = 'PyMca.spslut',
                         sources = ['PyMca/sps/Src/sps_lut.c',
                                    'PyMca/sps/Src/spslut_py.c'],
                         define_macros = define_macros,
                         include_dirs = ['PyMca/sps/Include'])
    ext_modules.append(module)
    if sys.platform != "win32":
        module = (Extension(name = 'PyMca.sps',
                                            sources = ['PyMca/sps/Src/sps.c',
                                                       'PyMca/sps/Src/sps_py.c'],
                                            define_macros = define_macros,
                                            include_dirs = ['PyMca/sps/Include']))
        ext_modules.append(module)

ext_modules = []
build_FastEdf(ext_modules)
build_specfile(ext_modules)
build_specfit(ext_modules)
build_sps(ext_modules)

# data_files fix from http://wiki.python.org/moin/DistutilsInstallDataScattered
from distutils.command.install_data import install_data
class smart_install_data(install_data):
    def run(self):
        global PYMCA_INSTALL_DIR
        #need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        PYMCA_INSTALL_DIR = self.install_dir
        print "PyMCA to be installed in %s" %  self.install_dir
        return install_data.run(self)

from distutils.command.install_scripts import install_scripts
class smart_install_scripts(install_scripts):
    def run (self):
        global PYMCA_SCRIPTS_DIR
        #I prefer not to translate the python used during the build
        #process for the case of having an installation on a disk shared
        #by different machines and starting python from a shell script
        #that positions the environment
        from distutils import log
        from stat import ST_MODE
        install_cmd = self.get_finalized_command('install')
        #This is to ignore the --install-scripts keyword
        #I do not know if to leave it optional ...
        if False:
            self.install_dir = os.path.join(getattr(install_cmd, 'install_lib'), 'PyMca')
            self.install_dir = os.path.join(self.install_dir, 'bin')        
        else:
            self.install_dir = getattr(install_cmd, 'install_scripts')
        PYMCA_SCRIPTS_DIR = self.install_dir        
        if sys.platform != "win32":
            print "PyMCA scripts to be installed in %s" %  self.install_dir
        self.outfiles = self.copy_tree(self.build_dir, self.install_dir)
        self.outfiles = []
        for filein in glob.glob('PyMca/scripts/*'):
            filedest = os.path.join(self.install_dir, os.path.basename(filein))
            if os.path.exists(filedest):
                os.remove(filedest)
            moddir = os.path.join(getattr(install_cmd,'install_lib'), "PyMca")
            f = open(filein, 'r')
            modfile = f.readline().replace("\n","")
            f.close()
            text  = "#!/bin/bash\n"
            text += "export PYTHONPATH=%s:${PYTHONPATH}\n" % moddir
            text += "exec python %s $*\n" %  os.path.join(moddir, modfile)
            f=open(filedest, 'w')
            f.write(text)
            f.close()
            #self.copy_file(filein, filedest)
            self.outfiles.append(filedest)
        if os.name == 'posix':
            # Set the executable bits (owner, group, and world) on
            # all the scripts we just installed.
            for file in self.get_outputs():
                if self.dry_run:
                    log.info("changing mode of %s", file)
                else:
                    mode = ((os.stat(file)[ST_MODE]) | 0555) & 07777
                    log.info("changing mode of %s to %o", file, mode)
                    os.chmod(file, mode)
   
description = ""
long_description = """
"""

distrib = setup(name="PyMca",
                license = "GPL - Please read LICENSE.GPL for details",
                version= __version__,
                description = description,
                author = "V. Armando Sole",
                author_email="sole@esrf.fr",
                url = "http://sourceforge.net/projects/pymca",
                long_description = long_description,
                packages = packages,
                platforms='any',
                ext_modules = ext_modules,
                data_files = data_files,
##                package_data = package_data,
##                package_dir = {'': 'lib'},
                cmdclass = {'install_data':smart_install_data, 
                            'install_scripts':smart_install_scripts},
                scripts=script_files,
                )



#post installation checks
try:
    import sip
    SIP = True
except ImportError:
    SIP = False
    print "sip must be installed for full pymca functionality."

badtext  = "No valid PyQt with qwt or PyQt4 with PyQwt5 installation found.\n"
badtext += "You will only be able to develop applications using  a very \n"
badtext += "small subset of PyMCA."
print "PyMCA is installed in %s " % PYMCA_INSTALL_DIR
if SIP:
    try:
        import PyQt4.QtCore
        QT4 = True
    except ImportError:
        QT4 = False
    except:
        QT4 = True

    try:        
        from PyQt4 import Qwt5
        QWT5 = True        
    except ImportError:
        QWT5 = False

    QT3  = False
    QWT4 = False
    if not QT4:
        try:
            import qt
            QT3 = True
        except ImportError:
            QT3 = False
        except:
	    pass

        try:
            import qwt
            QWT4 = True        
        except ImportError:
            QWT4 = False


    if QT4 and QT3:
        print "PyMCA does not work in a mixed Qt4 and qt installation (yet)"
        if QWT5:
            print "PyMCA is fully functional under PyQt with qwt."
            print "You have PyQt4 and PyQwt5 installed."
            print "That will be the preferred setup within one year."
            print "Batch fitting should already work."
            print "You can easily embed PyMCA fitting in your Qt4 graphical "
            print "applications using McaAdvancedFit.py"
        else:
            print badtext
    elif QT3 and not QWT4:
        print "PyMCA PyQt installations need PyQwt4"
        print badtext
    elif QT4 and QWT5:
        print "PyMCA is fully functional under PyQt with qwt."
        print "You have PyQt4 and PyQwt5 installed."
        print "That will be the preferred setup within one year."
        print "Batch fitting should work."
        print "You can easily embed PyMCA fitting in your Qt4 graphical "
        print "applications using McaAdvancedFit.py"
        if sys.platform != 'win32':
            print "Please make sure %s is in your path" % PYMCA_SCRIPTS_DIR
            print "and try the scripts:"
            for script in script_files:
                s = os.path.basename(script)
                if s.upper() == "PYMCA":continue
                if s.upper() == "MCA2EDF":continue
                print script
                                
    elif QT3 and QWT4:
        print "PyMCA installation successfully completed."
        if sys.platform != 'win32':
            print "Please make sure %s is in your path" % PYMCA_SCRIPTS_DIR
            print "and try the scripts:"
            for script in script_files:
                print os.path.basename(script)               
    else:
        print badtext
else:
    print "No valid PyQt with qwt or PyQt4 with PyQwt5 installation found."
    print "You will only be able to develop applications using  a very "
    print "small subset of PyMCA."
