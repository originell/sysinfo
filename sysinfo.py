#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hardware and software information collector for Linux.
"""

# Copyright (C) 2009 - Luis Nell

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import re
import platform
import subprocess
from datetime import timedelta

class System(object):
    """
    The holy system information collector
    """

    UPTIME_PATH = '/proc/uptime'
    LOADAVG_PATH = '/proc/loadavg'

    def info(self):
        """
        Get architecture, os-type, hostname, kernel, additional kernelinfos
        and the machinetype.

        Provided by the platform module
        """
        return platform.architecture()[:0] + platform.uname()[:5]

    def uptime(self):
        """
        Retrieve uptime.

        Returns a timedelta object
        """
        if os.path.exists(self.UPTIME_PATH):
            uptime_f = open(self.UPTIME_PATH).read().split()
            return timedelta(seconds=float(uptime_f[0]))

    def load(self):
        """
        Get the system\'s loadaverage.

        Return a tuple (usage over last minute, last 5 mins, last 10 mins)
        """
        load_f = open(self.LOADAVG_PATH).read().split()

        # number of processes and last process used is also in here..
        # do it?
        return (float(load_f[0]), float(load_f[1]), float(load_f[2]))

    def lspci(self):
        """
        Uses 'lspci' to retrieve detailed information about PCI buses and devices.

        Returns a list which contains dicts with id, type, name
        and rev for each device.
        """
        lspci = subprocess.Popen('lspci', stdout=subprocess.PIPE)
        lspci_val = lspci.communicate()[0].split('\n')

        device_list = []
        for device in lspci_val:
            m = re.match(r'(.+?) (.+): (.+) \((.*)\)',  device)
            if m:
                mgrp = m.groups()
                device_list.append({'id': mgrp[0], 'type': mgrp[1],
                                    'name': mgrp[2], 'rev': mgrp[3]})
        return device_list


class HDD(object):
    """
    The sane hddinfo processor
    """

    MTAB_PATH = '/etc/mtab'

    def __init__(self):
        self.mtabfile = open(self.MTAB_PATH)
        self.mtab = [x.split() for x in self.mtabfile]

    def info(self):
        """
        Get local partition/drive infos through unix\' statvfs signal.

        Returns a list containing a dict [{'free':XXX,..}]
        where the first hardrive is the first in mtab
        """
        hdds = []
        for hdd in self.mtab:
            if '/dev/' in hdd[0]:
                # See statvfs module doc for descriptions
                f_bsize, f_frsize, f_blocks, f_bfree = os.statvfs(hdd[1])[:4]
                hdds.append({'device': hdd[0], 'dir': hdd[1], 'blocksize': f_bsize,
                             'total': f_bsize*f_blocks, 'free': f_bsize*f_bfree})
        return hdds

class CPU(object):
    """
    The sane cpuinfo processor
    """

    CPUINF_PATH = '/proc/cpuinfo'
    CPU_STR = 'processor\t:'
    CPUS_DIR = '/sys/devices/system/cpu'
    CPUFREQ_DIR = '%s/cpu0/cpufreq' % CPUS_DIR

    def __init__(self):
        self.cpufile = open(self.CPUINF_PATH).read()

    def count(self):
        """
        Count available cores/cpus.
        """
        return self.cpufile.count(self.CPU_STR)

    def has_cpufreqd(self):
        """
        Detect if cpufreqd is installed.

        Needed for correct max. frequency
        """
        return os.path.exists(self.CPUFREQ_DIR)

    def info(self):
        """
        Converts CPUINF_PATH into a dict
        """
        cpus = self.count()

        infs = [x.split(': ') for x in self.cpufile.replace('\t', '').split('\n')][:-2]
        inf_list = []
        for i in xrange(cpus):
            inf_list.append({})
            for inf in infs:
                if inf[0] != '':
                    inf_list[i][inf[0].lower().lstrip()] = inf[1]
                    infs.remove(inf)
                else:
                    break
        return inf_list

    def maxfreq(self):
        """
        Detects the maximum frequencies per core.

        Returns a tuple containing frequencies per cpu/core in Megahertz
        """
        if self.has_cpufreqd():
            cpus = self.count()

            maxfreqs = ()
            i = 0
            while i <= cpus - 1:
                maxfreq = float(open('%s/cpu%i/cpufreq/cpuinfo_max_freq' % \
                                    (self.CPUS_DIR, i), 'r').read()) / 1024.00
                maxfreqs += (maxfreq,)
                i += 1
            return maxfreqs
        return False

class RAM(object):
    """
    The sane meminfo processor
    """

    RAMINF_PATH = '/proc/meminfo'

    def __init__(self):
        self.meminfo_raw = open(self.RAMINF_PATH)

    def info(self):
        """
        Converts RAMINFO_PATH into a dict

        Details in kilobyte
        """
        meminfos = {}
        for y in self.meminfo_raw:
            x = y.split(':')
            meminfos[x[0].lower()] = int(x[1].lstrip().replace(' kB', ''))
        return meminfos

class X(object):
    """
    The ugly Xserver information collector
    """
    def infos(self):
        """
        Retrieve Xorg infos from 'xdpyinfo'.

        This is some ugly piece of code
        """
        xdpy = subprocess.Popen('xdpyinfo', stdout=subprocess.PIPE)
        xdpy_val = xdpy.communicate()[0].split('\n')

        xinfos = {}
        curr_scr = 0
        for x in xdpy_val:
            m = re.match(r'(\S.+):\s+(.+)', x)
            if m:
                mgrp = m.groups()

                try:
                    xinfos[mgrp[0]] = int(mgrp[1])
                except ValueError:
                    xinfos[mgrp[0]] = mgrp[1]

            scr = re.match(r'screen #(\d+)', x)
            if scr:
                xinfos['screens'] = []
                curr_scr = int(scr.groups()[0])

            scrdetails = re.match(r'\s{2}(\w+.*):\s+(.*)', x)
            if scrdetails:
                scrdetails_grp = scrdetails.groups()

                try:
                    xinfos['screens'][curr_scr]
                except IndexError:
                    xinfos['screens'].append({})
                finally:
                    try:
                        xinfos['screens'][curr_scr][scrdetails_grp[0]] = int(scrdetails_grp[1])
                    except ValueError:
                        xinfos['screens'][curr_scr][scrdetails_grp[0]] = scrdetails_grp[1]
        return xinfos
