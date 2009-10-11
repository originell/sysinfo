=================
sysinfo
=================

--
is
--

a sane and easy to use library to collect/retrieve/access system informations under linux.

Tested on:
    * **2.6.31** - triple core cpu
    * **2.6.31** - single core cpu
    * **2.6.28** - single core cpu

Requirements
============

* python >= 2.5

Optional Requirements:
    * cpufreqd:
                for maximum cpu frequency detection to work
    * lspci:
             for pci device detection to work
    * X:
         the allmighty x server, otherwise you will not receive any X server information - who would have thought that O.o?!
