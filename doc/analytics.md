
# <a id='methods'>Analytic Method Descriptions</a>

  |Analytic Name|Name Agnostic?|Compiler Agnostic?|Partial matches?|Auto-handle new versions?|False Positives|
  | :-------------- | :----: | :----: | :----: | :----: | :----: |
  |[jar-name](#jar-name)         |    No    |   Yes    |    No     |    Yes    |    High    |
  |[jar-digest](#jar-digest)       |   Yes    |    No    |    No     |    No     |    No    |
  |[jar-fingerprint](#jar-fingerprint)  |   Yes    |   Yes    |    No     |    No     |Very Low   |
  |[class-digest](#class-digest)     |   Yes    |    No    |    Yes    |    No     |Partial: high, full: No|
  |[class-fingerprint](#class-fingerprint)|   Yes    |   Yes    |    Yes    |    No     |Partial: high, full: Low|


  -  <a id='jar-name'>'jar-name'</a> (Enabled by default)

     The 'jar-name' method uses regular expression matching of
     the jar file names to determine the version.  While this is
     not a reliable method, it is very fast, and can usually handle
     new versions of a jar file without any updates to the rules
     table it uses.  It also does not require a large configuration
     table, reducing the size of the Jaudit executable.

  -  <a id='jar-digest'>'jar-digest'</a> (Enabled by default)
  
     The 'jar-digest' method uses SHA256 digests of the individual
     class files within the jar file to create a single unique
     digest of the jar file.  It is susceptible to changes in the
     Java compiler used, but is immune to repackaging of the jar
     file (if no classes are added or removed).  As it has to read
     each class file, performance is not as fast as 'jar-name', but
     it also does not require a large configuration table.  It is
     not able to recognize versions that have not been added to
     the knowledge base.

  -  <a id='jar-fingerprint'>'jar-fingerprint'</a> (Enabled by default)

     The 'jar-fingerprint' method creates a
     [fingerprint](doc/fingerprints.md) for each class file using
     information extracted from the class file.  These fingerprints
     are then used to create a single fingerprint for the entire jar
     file.  As it has to decode each class file, performance is not as
     fast as 'jar-name', but it also does not require a large
     configuration table.  Performance is on par with
     'jar-digest'. The primary advantage is that it is resistant to
     changes to the compilation environment.  It is not able to
     recognize versions that have not been added to the knowledge
     base.

     
  -  <a id='class-digest'>'class-digest'</a> (Disabled by default)

     The 'class-digest' method uses SHA256 digests of each class file
     and then attempts to match each of those digests to determine
     where that class file is from originally.  Because many classes
     do not change between releases, a digest can match multiple
     versions.  The version that matches the most of these digests is
     selected.  If all of the digests are matched, 'class-digest' will
     report the match, otherwise it will indicate that the class files
     are embedded in another application.  This means it is able to
     recognize when an application is using a subset of class files
     from a library/application that Jaudit is looking for. It is
     sensitive to changes in the Java compiler. Because it needs the
     digests for every class, the configuration table is quite large
     and is therefore disabled by default. It can also report multiple
	 possible embedded versions if it is unable to match sufficient
	 digests to distinguish them.

  -  <a id='class-fingerprint'>'class-fingerprint'</a> (Disabled by default)

     The 'class-fingerprint' method extracts fingerprints using
     information extraced from each class file and then attempts to
     match each of those fingerprints to determine where that class
     file is from originally.  Because many classes do not change
     between releases, a fingerprint can match multiple versions.  The
     version that matches the most of these fingerprints is selected.
     If all of the fingerprints are matched, 'class-fingerprint' will
     report the match, otherwise it will indicate that the class files
     are embedded in another application.  This means it is able to
     recognize when an application is using a subset of class files
     from a library/application that Jaudit is looking for.  Because
     it needs the fingerprints for every class, the configuration
     table is quite large and is therefore disabled by default.
     It can also report multiple possible embedded versions if it is
	 unable to match sufficient	fingerprints to distinguish them.

