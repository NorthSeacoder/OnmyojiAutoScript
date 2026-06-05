@echo off
C:\Progra~1\Netease\MuMu\nx_device\12.0\shell\adb.exe kill-server
C:\Progra~1\Netease\MuMu\nx_device\12.0\shell\adb.exe start-server
C:\Progra~1\Netease\MuMu\nx_device\12.0\shell\adb.exe connect 127.0.0.1:5555
C:\Progra~1\Netease\MuMu\nx_device\12.0\shell\adb.exe connect 127.0.0.1:5557
C:\Progra~1\Netease\MuMu\nx_device\12.0\shell\adb.exe devices -l
