#!/usr/bin/env python3
#
#  Copyright (c) 2020, The OpenThread Authors.
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the copyright holder nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
import logging
import unittest

import config
import thread_cert

# Test description:
#   This test verifies bi-directional connectivity between Thread end device
#   and infra host.
#
# Topology:
#    ----------------(eth)--------------------
#           |                 |
#          BR1 (Leader)      HOST
#           |
#        ROUTER1
#

BR1 = 1
ROUTER1 = 2
HOST = 4

CHANNEL1 = 18

# The two prefixes are set small enough that a random-generated OMR prefix is
# very likely greater than them. So that the duckhorn BR will remove the random-generated one.
ON_MESH_PREFIX1 = "fd00:00:00:01::/64"
ON_MESH_PREFIX2 = "fd00:00:00:02::/64"


class SingleBorderRouter(thread_cert.TestCase):
    USE_MESSAGE_FACTORY = False

    TOPOLOGY = {
        BR1: {
            'name': 'BR_1',
            'allowlist': [ROUTER1],
            'is_otbr': True,
            'version': '1.2',
            'channel': CHANNEL1,
            'router_selection_jitter': 2,
        },
        ROUTER1: {
            'name': 'Router_1',
            'allowlist': [BR1],
            'version': '1.2',
            'channel': CHANNEL1,
            'router_selection_jitter': 2,
        },
        HOST: {
            'name': 'Host',
            'is_host': True
        },
    }

    def test(self):
        self.nodes[HOST].start(start_radvd=False)
        self.simulator.go(5)

        self.nodes[BR1].start()
        self.simulator.go(5)
        self.assertEqual('leader', self.nodes[BR1].get_state())

        self.nodes[ROUTER1].start()
        self.simulator.go(5)
        self.assertEqual('router', self.nodes[ROUTER1].get_state())

        self.simulator.go(10)
        self.collect_ipaddrs()

        logging.info("BR1     addrs: %r", self.nodes[BR1].get_addrs())
        logging.info("ROUTER1 addrs: %r", self.nodes[ROUTER1].get_addrs())
        logging.info("HOST    addrs: %r", self.nodes[HOST].get_addrs())

        self.assertGreaterEqual(len(self.nodes[HOST].get_addrs()), 2)

        self.assertTrue(len(self.nodes[BR1].get_prefixes()) == 1)
        self.assertTrue(len(self.nodes[ROUTER1].get_prefixes()) == 1)

        self.assertTrue(len(self.nodes[BR1].get_ip6_address(config.ADDRESS_TYPE.OMR)) == 1)
        self.assertTrue(len(self.nodes[ROUTER1].get_ip6_address(config.ADDRESS_TYPE.OMR)) == 1)
        self.assertTrue(len(self.nodes[HOST].get_ip6_address(config.ADDRESS_TYPE.ONLINK_ULA)) == 1)

        # Router1 can ping to/from the Host on infra link.
        self.assertTrue(self.nodes[ROUTER1].ping(self.nodes[HOST].get_ip6_address(config.ADDRESS_TYPE.ONLINK_ULA)[0]))
        self.assertTrue(self.nodes[HOST].ping(self.nodes[ROUTER1].get_ip6_address(config.ADDRESS_TYPE.OMR)[0],
                                              backbone=True))

        # Add two on-mesh prefix on BR1, so that
        # it will deregister its random-generated OMR prefix.
        self.nodes[BR1].add_prefix(ON_MESH_PREFIX1)
        self.nodes[BR1].add_prefix(ON_MESH_PREFIX2)
        self.nodes[BR1].register_netdata()

        self.simulator.go(10)
        self.collect_ipaddrs()

        logging.info("BR1     addrs: %r", self.nodes[BR1].get_addrs())
        logging.info("ROUTER1 addrs: %r", self.nodes[ROUTER1].get_addrs())
        logging.info("HOST    addrs: %r", self.nodes[HOST].get_addrs())

        self.assertGreaterEqual(len(self.nodes[HOST].get_addrs()), 2)

        self.assertTrue(len(self.nodes[BR1].get_prefixes()) == 2)
        self.assertTrue(len(self.nodes[ROUTER1].get_prefixes()) == 2)

        self.assertTrue(len(self.nodes[BR1].get_ip6_address(config.ADDRESS_TYPE.OMR)) == 2)
        self.assertTrue(len(self.nodes[ROUTER1].get_ip6_address(config.ADDRESS_TYPE.OMR)) == 2)
        self.assertTrue(len(self.nodes[HOST].get_ip6_address(config.ADDRESS_TYPE.ONLINK_ULA)) == 1)

        # Router1 can ping to/from the Host on infra link.
        self.assertTrue(self.nodes[ROUTER1].ping(self.nodes[HOST].get_ip6_address(config.ADDRESS_TYPE.ONLINK_ULA)[0]))
        self.assertTrue(self.nodes[HOST].ping(self.nodes[ROUTER1].get_ip6_address(config.ADDRESS_TYPE.OMR)[0],
                                              backbone=True))
        self.assertTrue(self.nodes[HOST].ping(self.nodes[ROUTER1].get_ip6_address(config.ADDRESS_TYPE.OMR)[1],
                                              backbone=True))


if __name__ == '__main__':
    unittest.main()
