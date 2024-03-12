
# Jaudit subcommand system

Jaudit provides additional subcommands for performing administrative tasks.  These
subcommands can be invoked using the ```run``` command in the ```bin``` subdirectory.

- [ansible-jaudit](#ansible-jaudit)
- [add-jars](#add-jars)
- [download-jars](#download-jars) (`auto` submodule)
- [rescan-jars](#rescan-jars) (`auto` submodule)
- [create-tables](#create-tables)
- [cve-annotate](#cve-annotate)
- [cve-download](#cve-download)
- [cve-extract](#cve-extract)
- [datasets](#datasets)
- [make-variants](#make-variants) (`builds` submodule)
- [rebuild-jaudit](#rebuild-jaudit)
- [report](#report)
- [submodules](#submodules)

## <a id="ansible-jaudit">ansible-jaudit</a>

To simplify running Jaudit on a large number of hosts, a utility is
provided to run Jaudit via ansible.  The subcommand 'ansible-jaudit'
use ansible to run Jaudit on the hosts specified in an ansible host
inventory file.  The basic usage is:

```
  bin/run ansible-jaudit --host-file <file-name>
```

An example ansible host inventory file is provided in the ansible
subdirectory.

'ansible-jaudit', as provided, will output a JSON record as a single
text line for each host.  Each JSON record will have a minimum of two
fields:

```
   status:  'ok', 'failed', or 'down'
   inventory_name:  <host name from inventory file>
```

A status of 'down' means the host could not be accessed. A status of
'failed' means that something went wrong during execution of Jaudit. Finally,
a status of 'ok' means that Jaudit executed successfully.  In this case,
the JSON record is the output from Jaudit as defined [here](jaudit_json.md).

### Ansible Host Groups

Support for ansibles host groups, for groups of hosts defined in the
inventory file, can be accessed using the --host-group option.  For example,

```
   bin/run ansible-jaudit --host-file <file-name> --host-group servers
```

will only audit hosts that are in the group 'servers'.


### Storing Results of Audit

The default behavior of ansible-jaudit is to write successful scan
results to stdout, and failed scan results to stderr.  However, you
can specify your own python classes which will be used for logging
the results.  This is done using the --storage-module option.  You
can specify multiple storage modules by providing the option multiple
times.

*NOTE*: The 'ansible' python module must be installed on the system that
is running 'ansible-jaudit'.

The storage module should be specified as
`package_name.Class?arg1=val&arg2=val...`.  The 'package\_name' is
the name of the package, and 'Class' is the name of a class in that
package.  Everything after the '?' are key value pairs that will be
passed to the \_\_init\_\_ method of the class.

Your class must have an \_\_init\_\_ method which accepts a dictionary
argument with the values from the command line (as discussed above). The
\_\_init\_\_ method should also do any one time initialization that is
needed.

```
    def init(self, **args):
	    pass
```

Your class must also specify a method named 'log' which receives a
single argument, which is the record from ansible:

```
    def log(self, record):
	    pass
```

An example storage module is provided in 'examples/ansible_sqlite3.py'.
A sample invocation (setting PYTHONPATH so python can find 'ansible\_sqlite3'):

```
PYTHONPATH=`pwd` bin/run ansible-jaudit --host-file hostfile \
    --storage-module \
      'examples.ansible_sqlite3.SQLiteLogger?dbname=jaudit.db&table=jaudit' 

```


## <a id="add-jars">add-jars</a>

### Adding new versions of jar files for supported libraries/applications.

To add a new version of a jar file, use the `add-jars`
subcommands. This command processes each jar-file specified on the
command line, extracting the information that the Jaudit
identification analytics need.  The extracted information is stored in
the dataset specified by the `-a` option.  This dataset needs to be
listed in the appropriate stanza in the `cf/datasets.json` file.

```
   bin/run add-jars -a jaudit.data/json/log4j log4j-5.0.0.jar
```

After adding new jar files, you must [rebuild](#rebuild-jaudit) Jaudit or
[rebuild](#create-tables) the Jaudit analytic data tables.

### Adding new libraries/applications.

To add a new library or application, you must add an entry to the file
`cf/monitored.json`.  This is JSON text file that describes the library.
A sample record at a minimal is of the form:

```
   "name-of-library": {
       "enabled": true,
       "description": "Brief description of the library",
       "vendor": "vendor name from CVE records",
       "cve-name": "Name of library in CVE records if different"
   }
```

See the documentation at the top of `cf/monitored.json` for more
details.

In addition, you need to add a record to the file `cf/datasets.json`.
For more information about datasets, see the [datasets](subcommands.md#datasets) subcommand. Only the `description` and `datasets` fields need to be
populated.  The `counts` field will be created.

## <a id="download-jars">download-jars</a>

(Requires the `auto` submodule be installed)

The `download-jars` subcommand is intended to be run periodically to check
for new versions of a library or application.  It can also be used to
populate the local jar repository when a new library or application is
created. It takes a single option, `--config` which specifies the config
file to use. An example is provided in the `auto` submodule in `cf/auto.cf`.

## <a id="rescan-jars">rescan-jars</a>

(Requires the `auto` submodule be installed)

The `rescan-jars` subcommand is used if there is a need to rebuild all of the
extracted data from scratch.  It has a single option, `--config` which specifies
the configuration file to use.  This is the same configuration file that
[download-jars](#download-jars) uses.

## <a id="create-tables">create-tables</a>

The `create-tables` subcommand is used to create the data tables that
the identifying analytics use. You can enable which identifying
analytics are to be supported by the tables, as well as enable or
disable specific Java libraries/applications. Available names can be
found using the [datasets list](#datasets) subcommand.  The default
status of the Java libraries and applications is controlled in the
file 'cf/monitored.json', but can be overridden on the command line.

The options for controlling `create-tables` are:

```
    -o filename     - Where to store the analytic data tables
	-a analytics    - A comma separated list of analytic names
	-e libraries    - A comma separated list of library/applications to enable
	-d libraries    - A comma separated list of library/applications to disable
	-c config       - Use different configuration (default cf/monitored.json)
	--pretty        - Format the JSON output (default if -o is used)
```	

## <a id="cve-annotate">cve-annotate</a>

When Jaudit is run, it does not include information about CVE records
associated with the identified versions.  However, this information can
be added during a post-processing step.  The tool

```
  bin/run cve-annotate
```

reads records from stdin and adds information about any relevant CVEs
to each record. Before this command can be used, you must first use
[cve-download](#cve-download) and [cve-extract](#cve-extract) to build
a local CVE repository.


## <a id="cve-download">cve-download</a>


In order for 'cve-annotate' to work, it must have a database of CVE records.
Two commands are provided to perform this:

```
   bin/run cve-download
```

is used to download the CVE information.  The first time it is run, this can
take around an hour.  Subsquent runs only download the new records.  This
should be run periodically to maintain the CVE locally.

It takes a single option, '-d' which specifies the directory where the CVE
reocrds are to be stored:

```
   bin/run cve-download -d /data/cve
```

cve-download should be run periodically to keep your local CVE repository up
to date. Each time, [cve-extract](#cve-extract) should be run to locate CVE
entries that are relevant to the Java libraries and applications that are
being monitored.

## <a id="cve-extract">cve-extract</a>


Whenever new CVE records are downloaded using
[cve-download](#cve-download), any entries that are relevant to the
libraries that are being monitored need to be extracted.  The tool
subcommand ```cve-extract``` is used for this.  It has one required
option:

```
     -d directory   -- The name of the directory where CVE data is stored.
                       This should be the same as provided in the download
 		               step.

     bin/run cve-extract -d /data/cve
```

'cve-extract' uses information from the file 'cf/monitored.json' to
identify which CVE records to extract.

The extracted relevant CVE records are written to the JSON file to
cf/cve_info.json. This file is what is used by
[cve-annotate](#cve-annotate) as described earlier.


## <a id="datasets">datasets</a>

When jar files are ingested, the information extracted from the jar
files is stored in datasets. These datasets are used to create the
tables used by Jaudit's versioning analytics. The 'datasets'
subcommand can be used to obtain information about these datasets.

```
   bin/run datasets list

   commons-compress  Apache Commons Compress
           [28 versions, 27 distinct, 1,613 distinct classes]
   elasticsearch     Elastic Search
           [372 versions, 370 distinct, 110,857 distinct classes]
   geotools          Geotools (gt-main)
           [232 versions, 190 distinct, 5,425 distinct classes]
   gson              Google GSON
           [36 versions, 33 distinct, 1,184 distinct classes]
   guava             Google Guava
           [84 versions, 103 distinct, 8,714 distinct classes]
   jackson-databind  FasterXML jackson-databind
           [190 versions, 190 distinct, 4,664 distinct classes]
   log4j             Apache Log4J v1 & v2, plus Apache Chainsaw
           [82 versions, 81 distinct, 6,513 distinct classes]
```

Of particular note are the distinct classes; these will determine how
large the 'jaudit.py' script will be if the corresponding dataset is
enabled when [rebuilding jaudit](#rebuild-jaudit) and either the
'class-fingerprint' or 'class-digest' analytics are enabled.

## <a id="rebuild-jaudit">rebuild-jaudit</a>

Jaudit is intended to be a single, monolithic script containing all of
the code and data tables.  This simplifies deployment, especially when
used in conjuction with Ansible.  Therefore, if any of the data tables
or code are updated, it will be necessary to rebuild the script.

The tool 'rebuild-jaudit' is used to build a new version
of jaudit/jaudit.py.  Part of this process involves selecting the
minimum set of fingerprints needed for identifying all of the versions.
This step can take some time to perform the analysis.  Invocation is:

```
  bin/run rebuild-jaudit 
```

Once completed, the new version of jaudit.py is ready for use in the
'jaudit' directory. You can specify the output file name using the
'-o' option. The default is './jaudit.py'. In addition, you can enable
which identifying analytics you want, as well as enable or disable
specific Java libraries/applications. Available names can be found
using the [datasets list](#datasets) subcommand.  The default status
of the Java libraries and applications is controlled in the file
'cf/monitored.json', but can be overriden.  The options for
controlling 'rebuild-jaudit' are:

```
    -o filename     - Where to store the output script
	-a analytics    - A comma separated list of analytic names
	-e libraries    - A comma separated list of library/applications to enable
	-d libraries    - A comma separated list of library/applications to disable
	
	
   bin/run rebuild-jaudit -o jaudit_base.py
   bin/run rebuild-jaudit -o jaudit_all.py -a jar-name,jar-digest,jar-fingerprint,class-fingerprint,class-digest -e commons-compress,elasticsearch,geotools,gson,guava,jackson-databind,log4j
```

The individual identification analytics available are:

- [jar-name](analytics.md#jar-name) Regular expression based identification.

- [jar-digest](analytics.md#jar-digest) SHA256 based identification

- [jar-fingerprint](analytics.md#jar-fingerprint) Fingerprint-based identification.

- [class-digest](analytics.md#class-digest) Individual class SHA256 based identification.

- [class-fingerprint](analytics.md#class-fingerprint) Individual class fingerprint based identification.

## <a id="report">report</a>

The Jaudit report generator subcommand 'report' is used to convert the JSON
output to either a text report or an HTML report. It reads the JSON from stdin
and outputs the result to stdout. The usage is:

```
   bin/run report [--mode text|html] [--no-color]
```

The option '--mode' selects either text or HTML mode.  The default is text
mode. If the JSON has been annotated by [cve-annotate](#cve-annotate), then
the output will be color coded based on the severity of the CVEs.  The
--no-color option disables color coding.


## <a id="submodules">submodules</a>

Jaudit consists of a main Git repo (jaudit) and multiple optional
submodules.  The git submodule layout is shown below. Note that these
are not managed as actual "true" Git submodules. When they are added,
the submodule is simply 'cloned'.

```
jaudit + 
       |
       |
       + jaudit.python     -- [python] Python source code for Jaudit
       |
       |
       + jaudit.data       -- [data] Fingerprint/Digest data from jar files
       |
       |
       + jaudit.pybuilds   -- [builds] Alternate Python builds of Jaudit       |
       |
       |
       + jaudit.auto       -- [auto] Automatic update/build of Jaudit
       |
       |
       + jaudit.test       -- [test] Testing for jaudit
```

The subcommand 'submodules' can be used to manage the submodules.  Use

```   bin/run submodules list

      auto[N]          git@github.ibm.com:software-genome/jaudit-auto.git
                       Automatically download and process new jar files and CVE data.

      builder[N]       git@github.ibm.com:software-genome/jaudit.builder.git
                       Tooling to automatically rebuild Jaudit.

      builds[N]        git@github.ibm.com:software-genome/jaudit.pybuilds.git
                       Prebuilt Jaudit builds for deployment.

      data[N]          git@github.ibm.com:software-genome/jaudit.data.git
                       Precomputed fingerprints and hashes for various Java libraries
                       and applications.

      python[N]        git@github.ibm.com:software-genome/jaudit.python.git
                       Python source for rebuilding Jaudit's 'jaudit.py'.

```

to see the list of submodules and whether they are installed.  To add
a submodule, use:

```
   bin/run submodules add <name>
```

where <name> is a name from the list of submodules.  For example, to install
the submodule 'builds', use:

```
   bin/run submodules add builds
```
