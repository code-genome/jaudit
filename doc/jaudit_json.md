

# Jaudit JSON Format Description

The default output of Jaudit is a sequence of JSON objects, each on a
separate line.  The format of each JSON record is:

```
{
   "type": "<type-of-input>",    // jar/jpi/war/ear/tar/tgz/container/volume/image
   "name": "<name-of-input>",    // Typically a file name
   "comment":"<per-type-info>",  // Optional additional information
   "versions": [                 // List of version information (optional)
       {
          "version":"<version-id>",         // The actual version string
          "analytics":["<analytic-name>"],  // List of analytics that identified the version
       }
   ],
   "children": [   // Contained inputs
      {...}        // This will be a list of JSON objects with the same structure
                   // as the parent.  This is used if an input is found
                   // inside another input, such as a 'tar' file.  Processing
                   // should be applied recursively as long as the 'children'
                   // field exists.
   ]
}
```

The 'versions' field will only be present if any Java library or application versions
were identified.

In addition to the basic record above, if the JSON has been annotated
with cve-annotate, then each entry in the 'versions' list, *may* also
contain the relevant CVE information.:

```
      "cve" : [                      // List of associated CVEs (optional)
         {
           "id":"<CVE-ID>",          // The actual CVE identifier
           "severity":<level>",      // CRITICAL, HIGH, LOW, etc
           "score":score,            // The score, 0.0-10.0 assigned to CVE by NVD
           "epss": {
              "percentile": rank,    // Percentile rank from EPSS
              "score":score          // Score assigned by EPSS
           },
           "versions": {             // Start-End version for this CVE
              "end": "end-version",  // Ending version
              "start": "start-version", // Starting version
              "end_op": "op"         // Either '<' or '<=', applied to "end"
           },
           "cisa_kev": {             // Date information
              "date":"yyyy-mm-dd",   // When CISA KEV added this CVE
              "due":"yyyy-mm-dd"     // Target date to have all systems patched
           }
         },
         ...
      ]
```

Even when CVE records are present, the "epss" and "cisa_kev" fields may not exist,
as they do not cover 100% of all CVEs.


## Example JSON output:

```
{
    "children": [
        {
            "name": "/opt/lib/jars/log4j-core-2.3.1.jar",
            "type": "jar",
            "versions": [
                {
                    "analytics": [
                        "jar-fingerprint"
                    ],
                    "cve": [
                        {
                            "epss": {
                                "percentile": 0.97788,
                                "score": 0.74805
                            },
                            "id": "CVE-2017-5645",
                            "score": 9.8,
                            "severity": "CRITICAL",
                            "versions": {
                                "end": "2.8.2",
                                "end_op": "<",
                                "start": "2.0"
                            }
                        },
                        {
                            "epss": {
                                "percentile": 0.90998,
                                "score": 0.03957
                            },
                            "id": "CVE-2021-44832",
                            "score": 6.6,
                            "severity": "MEDIUM",
                            "versions": {
                                "end": "2.3.2",
                                "end_op": "<",
                                "start": "2.0.1"
                            }
                        },
                        {
                            "cisa_kev": {
                                "date": "2023-05-01",
                                "due": "2023-05-22"
                            },
                            "epss": {
                                "percentile": 0.99903,
                                "score": 0.9741
                            },
                            "id": "CVE-2021-45046",
                            "known_exploited": true,
                            "score": 9.0,
                            "severity": "CRITICAL",
                            "versions": {
                                "end": "2.12.2",
                                "end_op": "<",
                                "start": "2.0.1"
                            }
                        }
                    ],
                    "evidence": [
                        {
                            "analytic": "jar-fingerprint",
                            "evidence": [
                                "Fingerprint matched c2dc0c"
                            ]
                        }
                    ],
                    "version": "log4j-core-2.3.1"
                }
            ]
        }
    ],
    "comment": "python3",
    "name": "jaudit-test-host",
    "type": "host"
}
```
