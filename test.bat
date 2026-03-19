@echo off
"C:\Program Files\nodejs\node.exe" -v > test_out.txt
"C:\Program Files\nodejs\npx.cmd" -v >> test_out.txt
"C:\Program Files\nodejs\npx.cmd" --yes skills add pbakaus/impeccable >> test_out.txt 2>&1
