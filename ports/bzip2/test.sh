# Compresses a copy of the test file and lists what it did.
$ run Data:/Programs/bzip2/bin/bzip2 -kv test/words.txt
> test/words.txt:
= 0
$ run Data:/Programs/bzip2/bin/bzip2 -tv test/words.txt.bz2
> ok
= 0
