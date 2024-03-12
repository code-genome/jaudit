# Jaudit

## What is Jaudit?

Jaudit is a tool for determining the release version of Java jar
files.  It's primary purpose is to locate versions that have known
serious security vulnerabilities.  It was originally developed to
reliably identify the vulnerable versions of 'log4j', but can handle
other Java libraries/applications besides 'log4j'.
  
Jaudit can scan running process or search the filesystem for jar
files. It can also optionally search inside of various archive
formats, such as zip, tar, etc., to locate jar files.  This support
streams the archives and does not require extracting to local storage.
Support for scanning Docker containers, images and volumes is also
available.
  
Give it a quick try, scanning any currently running Java processes:
  
```
     python bin/jaudit.py --running --report
```

You can also point it to specific jar files:

```
     python bin/jaudit.py /path/to/some.jar
```
  
or scan your filesystem (this may take a while):
  
```
     python bin/jaudit.py -F / --report
```
  
The '--report' option produces a text version of the output. Without
the '--report' option, Jaudit outputs the results
as [JSON](doc/jaudit_json.md) so that the output can easily be consumed
by other tooling. The [report](doc/subcommands.md#report) subcommand
can be used at the end to generate a text report. In addition, it
gives more control over the format of the output than the '--report'
option.
  

In addition to identifying the version of the Java
libraries/applications, tooling is provided to annotate the output
records with relevant CVE records to allow identifying vulnerable
versions.  This requires maintaining a local CVE repository, as
described in the [Jaudit CVE documentation](doc/subcommands.md#cve-annotate). Once you have
initialized a local CVE repository, you can use:
  
```
python bin/jaudit.py --running | bin/run cve-annotate | bin/run report
```

Jaudit has no required external dependencies, and can be executed
using either Python 2 or Python 3. It can easily be deployed using
[Ansible](doc/subcommands.md#ansible-jaudit) (requires that the Python
'ansible' module be installed).

Jaudit provides multiple methods of determining the release version,
with differing pros and cons.  The table below summarizes them.  The
methods they use are described in [Analytic Method Descriptions](doc/analytics.md).

This Jaudit repository comes with a prebuilt jaudit.py in
bin/jaudit.py.  This prebuilt version has 'jar-name', 'jar-digest' and
'jar-fingerprint' enabled.  It only supports identifying 'log4j'.
This is to keep the size of the script small.

Jaudit is a single, completely self-contained, script, to enable easy
deployment remotely without having to install anything.  This is of
particular benefit when Jaudit is used with 'ansible'.

  
## Subcommands

This repository also comes with support for rebuilding Jaudit with
support for the other analytics, or adding other
libraries/applications.  The interface for executing
[subcommands](doc/subcommands.md) is './bin/run'.  Use

```
./bin/run --list
```

to show a list of subcommands. The additional documentation also
includes instructions on how to use the subcommands.  In addition,
there are additional Git repositories which can be added.
  
