'''
This module contains tooling to generate an rpm package.
'''
# pylint: disable-msg-cat=WCREFI
#@PydevCodeAnalysisIgnore

import subprocess
import os
import sys
import shutil
import shutil

pwd = os.getcwd()

#get subversion version number of the repository
svn = subprocess.Popen(["svnversion","."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
svnversion = svn.communicate()[0]
svnversion = svnversion.strip()

projectname   = "process_explorer"
versionprefix = "0.2"


def createFullPath(thepathlist):
  fullpath = ""
  for p in thepathlist.split(":"):
    if p != "":
      fullpath = fullpath + "/opt/" + projectname + '-' + versionprefix + '-' + svnversion + "/" + p + ":"
  return fullpath

pwd = os.getcwd()
#
#Create RPM 'environment'
#
subprocess.check_call(["/bin/rm", "-rf", "./rpm"])
subprocess.check_call(["/bin/rm", "-rf", "./i386"])
os.mkdir("./rpm")
os.mkdir("./rpm/BUILD")
os.mkdir("./rpm/RPMS")
os.mkdir("./rpm/SOURCES")
os.mkdir("./rpm/SPECS")
os.mkdir("./rpm/SRPMS")
#
# Build the RPM which installs all software on target
#
subprocess.check_call(["rpmbuild", 
   "-bb", 
   "--define", "_topdir "+pwd  + "/rpm", 
   "--define", "_svnversion "  + svnversion, 
   "--define", "_projectname " + projectname, 
   "--define", "_versionprefix " + versionprefix,
   "process_explorer.spec"])

#   "--define", "_pythonpath "  + createFullPath(pythonpath),

subprocess.check_call(["mv", pwd + '/rpm/RPMS/i386/'+projectname + '-' + versionprefix + '-' + svnversion + ".i386.rpm", "."])

#create .tar.gz file for rpmless setup..

subprocess.check_call(["tar", "-C", pwd + "/rpm/BUILD/opt", "-cvzf", projectname + '-' + versionprefix + '-' + svnversion + ".tar.gz", projectname + '-' + versionprefix + '-' + svnversion])


#remove stuff
subprocess.check_call(["/bin/rm", "-rf", "./rpm"])

print "********************************************"
print "RPM file is : " + pwd + '/rpm/RPMS/i386/'+projectname + '-' + versionprefix + '-' + svnversion + ".i386.rpm"
print "********************************************"
    
