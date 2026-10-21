-- STELA port test for Lua.
print("lua: hello from " .. _VERSION)
local function fact(n) if n <= 1 then return 1 end return n * fact(n - 1) end
print("lua: 10! = " .. fact(10))
local co = coroutine.wrap(function() for i = 1, 3 do coroutine.yield(i * i) end end)
print("lua: coroutine " .. co() .. " " .. co() .. " " .. co())
local f = assert(io.open("/tmp/lua.txt", "w"))
f:write("written by lua\n")
f:close()
print("lua: file says " .. io.open("/tmp/lua.txt"):read("l"))
print(string.format("lua: os.time %s", os.time() > 1700000000 and "ok" or "bad"))
