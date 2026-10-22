call setline(1, "written by vim on STELA")
call append(1, "line two")
write! test/vim.txt
quit!
