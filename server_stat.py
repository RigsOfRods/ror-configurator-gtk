#!/usr/bin/python
# This source file is part of Rigs of Rods
# Copyright 2015 Artem Vorotnikov

# For more information, see http://www.rigsofrods.com/

# Rigs of Rods is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.

# Rigs of Rods is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Rigs of Rods.  If not, see <http://www.gnu.org/licenses/>.

import ast
from html.parser import *
import requests

import ping

ROR_NET = 'RoRnet_2.37'
MASTER_URL = 'http://api.rigsofrods.com/serverlist/?version=' + ROR_NET
FORMAT = (["<table border='1'><tr><td><b>Players</b></td><td><b>Type</b></td><td><b>Name</b></td><td><b>Terrain</b></td></tr>", ""],
          ["rorserver://", ""],
          ["user:pass@", ""],
          ["<td valign='middle'>password</td>", "<td valign='middle'>True</td>"],
          ["<td valign='middle'></td>", "<td valign='middle'>False</td>"])

# Layout for table no: ----- 1 --- 2 --- 3 ---
MASTER_PLAYER_COLUMN =      [1,    None, None]
MASTER_PLAYERCOUNT_COLUMN = [None, 1,    1   ]
MASTER_PLAYERLIMIT_COLUMN = [None, 2,    2   ]
MASTER_PASS_COLUMN =        [2,    3,    3   ]
MASTER_HOST_COLUMN =        [3,    4,    4   ]
MASTER_NAME_COLUMN =        [4,    5,    5   ]
MASTER_TERRAIN_COLUMN =     [5,    6,    6   ]
MASTER_PING_COLUMN =        [None, None, 7   ]
# Columns of table no: ----- 1 --- 2 --- 3 ---
MASTER_TABLE_WIDTH =        [5,    6,    7   ]


class ServerListParser(HTMLParser):
    """The HTML Parser for Master server list retrieved from MASTER_URL"""
    list1 = []
    list2 = []
    parser_mode = 0

    def handle_data(self, data):
        """Normal data handler"""
        if self.parser_mode == 0:
            if data == "Full server":
                self.parser_mode = 1
            else:
                self.list1.append(data)
        elif self.parser_mode == 1:
            self.list2.append(data)

    def handle_starttag(self, tag, value):
        """Extracts host link from cell"""
        if tag == "a":
            self.list1.append(value[0][1].replace("/", ""))


def format_server_tuple(array, entry_length, player_column, pass_column):
    """Splits player column into total and max players.
    Converts password info to bool
    """
    array2 = []
    array2.append([])

    for j in range(len(array)):
        if j % entry_length == (player_column - 1):
            array2[-1].append(int(array[j].split('/')[0]))
            array2[-1].append(int(array[j].split('/')[1]))
        elif j % entry_length == (pass_column - 1):
            array2[-1].append(ast.literal_eval(array[j]))
        else:
            array2[-1].append(array[j])

    return array2[0]

def list_to_table(array, width):
    """Converts the list into a table"""
    array2 = []
    array2.append([])
    i = 0

    for j in range(len(array)):
        array2[-1].append(array[j])

        if i < (width-1):
            i += 1
        elif j+1 < len(array):
            array2.append([])
            i = 0
    return array2


def append_rtt_info(array, host_column, bool_ping):
    """Appends server response time to the table. If bool_ping is set to false, print 9999 instead."""
    hosts_array = []
    rtt_temp_array = []
    rtt_temp_array.append([])
    rtt_array = []
    rtt_array.append([])

    for i in range(len(array)):
        hosts_array.append(array[i][host_column].split(':')[0])

    pinger = ping.Pinger()
    pinger.thread_count = 16
    pinger.hosts = hosts_array

    if bool_ping is True:
        pinger.status.clear()
        rtt_temp_array = pinger.start()

        rtt_array = list_to_table(rtt_temp_array[0], 2)

        # Match ping in host list. Beware: this is a crude search algorithm with O(2) complexity.
        for i in range(len(array)):
            for j in range(len(rtt_array)):
                if rtt_array[j][0] == array[i][host_column].split(':')[0]:
                    array[i].append(rtt_array[j][1])
                    break

    else:
        for i in range(len(hosts_array)):
            array[i].append(9999)

    return


def stat_master(url, bool_rtt):
    """Stats the master server"""
    ServerListParser.list1.clear()
    stream = requests.get(url).text

    for i in range(len(FORMAT)):
        stream = stream.replace(FORMAT[i][0], FORMAT[i][1])

    parser = ServerListParser()
    parser.feed(stream)

    ServerListParser.list1 = list_to_table(format_server_tuple(ServerListParser.list1, MASTER_TABLE_WIDTH[0], MASTER_PLAYER_COLUMN[0], MASTER_PASS_COLUMN[0]), MASTER_TABLE_WIDTH[1])
    append_rtt_info(ServerListParser.list1, MASTER_HOST_COLUMN[1] - 1, bool_rtt)

    return ServerListParser.list1
