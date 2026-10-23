# STELA port test for BusyBox (its ash runs this).
cd /tmp
mkdir -p bbtest && cd bbtest
printf 'banana\napple\ncherry\napple\n' > fruit.txt
echo "busybox: sorted $(sort -u fruit.txt | tr '\n' ' ')"
echo "busybox: awk sum $(seq 1 10 | awk '{s += $1} END {print s}')"
echo "busybox: sed $(echo hello world | sed 's/world/STELA/')"
echo "busybox: grep $(grep -c apple fruit.txt)"
tar czf ../bb.tgz fruit.txt && rm fruit.txt && tar xzf ../bb.tgz
echo "busybox: tar kept $(wc -l < fruit.txt) lines"
gzip -c fruit.txt | gunzip | md5sum | cut -c1-8 > sum1
md5sum < fruit.txt | cut -c1-8 > sum2
cmp -s sum1 sum2 && echo "busybox: gzip round trip ok"
ls | xargs echo "busybox: ls"
echo "busybox: done"
