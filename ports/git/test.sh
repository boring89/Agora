# A repository in Data:/test/repo: init, add, commit, log; then a copy.
$ run Data:/Programs/git/bin/git --version
> git version 2.47.0
= 0
$ run Data:/Programs/git/bin/git init -q test/repo
= 0
$ cp test/hello.txt test/repo/hello.txt
$ run Data:/Programs/git/bin/git -C test/repo add hello.txt
= 0
$ run Data:/Programs/git/bin/git -C test/repo -c user.name=stela -c user.email=stela@example.org commit -q -m first
= 0
$ run Data:/Programs/git/bin/git --no-pager -C test/repo log --oneline
> first
= 0
$ run Data:/Programs/git/bin/git clone -q --no-hardlinks test/repo test/copy
= 0
$ cat test/copy/hello.txt
> hello from git on STELA
