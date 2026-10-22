$ run Data:/Programs/ripgrep/bin/rg --version
> ripgrep 15.2.0
= 0
$ run Data:/Programs/ripgrep/bin/rg -n --no-heading --sort path fox /Data/test
> fox.txt:1:The quick brown fox
> fox.txt:3:foxes are quick
> b.txt:2:but a fox here
= 0
$ run Data:/Programs/ripgrep/bin/rg -c zebra /Data/test
= 1
