
# Jaudit's Fingerprinting

Jaudit has two analytics, `jar-fingerprint` and `class-fingerprint` which uses a fingerprinting
technique to identify versions. The fingerprint is derived from information extracted from the
class files.  The difference between them is that `jar-fingerprint` uses a single fingerprint that
identifies the jar-file, where-as `class-fingerprint` maintains a fingerprint for every class file
that has been added to the system.  This allows class-fingerprint to recognize class files that are
embedded in other jar files.

The information extracted from the class files is selected to minimize the impact of compiler
options and versions. The following is a list of the types of information extracted
from the class files:

- class name and flags (`public`, etc)
- parent class name
- implemented interface names
- field names, including field descriptor and flags (`public`, `static`, etc)
- method names, including method descriptor and flags (`public`, `static`, etc)
- Any string constants in the constant pool
- Any integer or floating point constants in the constant pool
- Any field references, including field descriptor
- Any method references, including descriptor

In some instances, individual entries may be ignored.  For example, anything that is
marked as `synthetic` is not used.  Currently the fingerprint does not include any information
from attribute fields in the class file; this may change in the future.

After extracting all of these piece of information, they are sorted and a SHA256 is computed
across them.  This is the `class-fingerprint`.  After all of the `class-fingerprint`s have
been collected from a jar file, and a SHA256 is computed over the sorted fingerprints, which
is the `jar-fingerprint`.
