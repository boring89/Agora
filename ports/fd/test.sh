$ run Data:/Programs/fd/bin/fd --version
> fd 10.5.0
= 0
$ run Data:/Programs/fd/bin/fd --color never -e md readme /Data/test
> /Data/test/docs/readme.md
= 0
$ run Data:/Programs/fd/bin/fd --color never -e txt notes /Data/test
> /Data/test/notes.txt
= 0
