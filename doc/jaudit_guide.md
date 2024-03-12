
# Jaudit User Guide
## Table of Contents


- Introduction
-- What is Jaudit?
-- Basic Jaudit Usage
-- 

# Introduction

## What is Jaudit?

Jaudit is a tool for determining the release version of Java libraries
and applications.  It provides a variety of different methods for
determining the version, with different pros and cons. Jaudit was
originally created to identify the version of 'log4j' in response to
the 'Log4Shell' exploit.  However, it is not limited to
'log4j'. However, the build of Jaudit in this repo only contains
support for 'log4j'.  Support for other Java libraries and
applications is available in a separate repo.  It is also
straightforward to add support for new Java libraries and
applications.

Jaudit is distributed as a single monolithic Python script.  This is
to enable easy deployment, as it is not necessary to install it. It
also uses only the base Python packages. The only requirement is that
Python is installed. It can be run simply by copying the script to a
target system. It has been tested on Linux, MacOS, AIX and Windows.

## Basic Jaudit Usage

### Audit running Java applications

The first audit to perform is to check any running Java applications
to see if they are using versions of Java library jars that are known
to have security vulnerabilities.  *** Please note that out of the
box, Jaudit only checks for 'log4j'.  For other libraries, you will
need to [rebuild Jaudit](subcommands.md#rebuild-jaudit) or
[add the new libraries](subcommands.md#add-jars).


To check running applications, use the following command:

```
   python bin/jaudit.py --running --report > jaudit_running.txt
```

If you prefer [JSON](jaudit_json.md) output for consumption by other applications, do not use
the --report option:

```
   python bin/jaudit.py --running > jaudit_running.json
```

If an application is found using any of the libraries that are checked, the
output will look similar to this:

```
host:host.example.com
   +--> process:LogTest[7381]
             +--> jar:/opt/app/jars/log4j-core-2.3.1.jar
                  +--> version:log4j-core-2.3.1 [class-fingerprint]
```
This is indicating that on host 'host.example.com', in process 7381, which
is running 'LogTest', the jar file /opt/app/jars/log4j-core-2.3.1.jar' is
being used which has version 'log4j-core-2.3.1'.

## Scan file systems for Java applications

Following scanning running processes, it is important to also scan the
filesystems to discover other applications that use unsafe versions of the
monitored Java libraries.  To do this, use the following command:

```
   python bin/jaudit.py --search --report > scan_results.txt
```

As before, if the --report option is excluded, the output will be in
JSON format.  Jaudit will only scan local file systems.  Network file systems
will not be scanned.  If you only want to scan specific points in the
file system tree, then use

```
   python bin/jaudit.py --file-system /starting/point
```

You can include multiple directories to start in by either specifying the
option multiple times, or providing a comma separate list of starting points:

```
   python bin/jaudit.py --file-system /lib,/usr/lib,/opt,/usr/local,
```

You can also specify stopping points if you want to exclude certain
directories by using the --prune-fs option.  This may be necessary if
Jaudit fails to detect that a remote file system exists:

```
   python bin/jaudit.py --file-system /opt --prune-fs /opt/remote
```

In addition, Jaudit always attempts to recognize network or remote
file systems and will not scan them.

## Searching inside archive file types


Jaudit supports looking inside of 'tar' and 'zip' files.  These options
are off by default.  When enabled, the scan will recursively dig into
'zip' and 'tar' files, looking for Java applications.  This means that
if a 'zip' file contains a 'tar' file which contains another 'tar' file
that contains a 'zip' file, which contains a 'tar' file which contains
the Java application, Jaudit will find it.  To enable these, use the
'--scan-tarfiles' and '--scan-zipfiles' options.  If any applications
are found, the output will indicate the path to the application:

```
host:test-host
  └──zip:/test/jars/ziptest4.zip
       └──tar:tartest3.tar
            └──zip:ziptest1.zip
                 └──jar:apache/log4j-core-2.13.2.jar
                      ├──version: log4j-core-2.13.3
                      └──version: log4j-core-2.13.2
```

For JSON output, the structure for nested files is described
[here](jaudit_json.md).

## Searching docker images and containers

Jaudit can also search docker images, running docker containers, as well
as docker volumes.  Note that docker volumes may also be scanned if using
the previously described options for scanning the file system, as the volumes
are typically directories within the filesystem.  To enable this option,
simply use the '--scan-docker' option:

```
   python bin/jaudit.py --scan-docker
```

All running docker containers, local docker images, and local docker volumes
will be scanned.  Note that this option requires 'docker' to be installed,
or 'podman' with 'docker' replacement commands.

## Additional options

```
usage: jaudit.py [-h] [-r] [-s] [--system-packages] [-F FILE_SYSTEM] [-v]
                 [-D SCAN_DOCKER] [-T] [-Z] [-H HOSTNAME] [-e ENABLE]
                 [--prune-fs PRUNE_FS] [-a] [--list-analytics] [--full]
                 [--no-evidence] [--report]
                 [file [file ...]]

positional arguments:
  file

optional arguments:
  -h, --help            show this help message and exit
  -r, --running         Analyze running processes.
  -s, --search          Scan mounted file systems.
  --system-packages     Use system package manager to quickly locate candidate
                        files.
  -F FILE_SYSTEM, --file-system FILE_SYSTEM
                        Scan a specific file-system/directory.
  --analytic-data ANALYTIC_DATA
                        Specify alternate analytic data file to load.
  -v, --verbose         Show information about what is going on.
  -D SCAN_DOCKER, --scan-docker SCAN_DOCKER
                        Scan docker containers,images or volumes.
  -T, --scan-tarfiles   Scan any tar files that are discovered.
  -Z, --scan-zipfiles   Scan any zip files that are discovered.
  -H HOSTNAME, --hostname HOSTNAME
                        Specify the hostname to use in the output record.
  -e ENABLE, --enable ENABLE
                        Enable specific analytic; use --list-analytics for
                        names of analytics.
  --prune-fs PRUNE_FS   Do not allow file system scans to scan the specified
                        file-system/directory.
  -a, --list-applications
                        List the applications that are checked.
  --list-analytics      List the available analytics for use with --enable.
  --full                Give full description of each analytic.
  --no-evidence         Don't include evidence field in version records.
  --report              Send JSON through report generator.

```
