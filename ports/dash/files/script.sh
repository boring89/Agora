# STELA port test for dash: variables, loops, functions, pipes,
# command substitution, subshells, exit codes, programs run by path.
total=0
for i in 1 2 3 4; do total=$((total + i)); done
echo "dash: total $total"
greet() { echo "dash: hello, $1"; }
greet STELA
echo "dash: $(echo nested | tr a-z A-Z 2>/dev/null || echo NESTED)"
( exit 3 ); echo "dash: subshell exited $?"
/Data/Programs/dash/bin/dash /Data/test/sub.sh piped | while read line; do case "$line" in hello*) echo "dash: got $line";; esac; done
if [ -d /Data/test ]; then echo "dash: test folder exists"; fi
cd /tmp && echo "dash: cwd $(pwd)"
