#!/usr/bin/python
'''
Ansible module

This module will be called to wait until SHC is completely setup and 
initial bundle replication has occurred such that user defined 
bundles are safe to push
'''
import time
import json 
import requests

from ansible.module_utils.basic import AnsibleModule

class ShcReady(object):
    def __init__(self, module):
        self.captain_url = module.params["captain_url"]
        self.shc_peers = module.params["shc_peers"]
        self.user = module.params["spl_user"]
        self.password = module.params["spl_pass"]
        self.retry_times = module.params["retry_times"]

    def run(self):
        URL = "https://{0}:8089/services/shcluster/status?output_mode=json".format(self.captain_url)
        peers_online = False
        peers_ready = False 
        time.sleep(60) # give the SHC some initial time to setup
        online_peers = None 
        for _ in range(0, self.retry_times):
            time.sleep(30) # wait some time before executing next loop
            try:
                resp = requests.get(URL, auth=(self.user, self.password), verify=False).json()
                if not peers_online:
                    shc_peers = resp['entry'][0]['content']['peers']
                    if len(shc_peers.keys()) == (len(self.shc_peers) + 1): # SH Captain included in list
                        peers_online = True
                if not peers_ready:
                    shc_peers = resp['entry'][0]['content']['peers']
                    online_peers = [peer for peer in shc_peers if shc_peers[peer].get('last_conf_replication', None) != "Pending"] 
                    if len(online_peers) == (len(self.shc_peers) + 1): # SH Captain included in list
                        peers_ready = True
                if peers_online and peers_ready:
                    break 
            except Exception as e:
                pass 
        if not (peers_online and peers_ready):
            raise Exception("SHC failure, setup time exceeded set limits.  peers_ready:{0}, peers_online:{1}, online_peers:{2}".format(peers_ready, peers_online, online_peers))

        return {1:self.captain_url, 2:self.shc_peers, 'two':str(type(self.shc_peers)), 3: self.user, 4: self.password, 5:shc_peers, 6:shc_peers.keys(), 7:online_peers}

def main():
    module = AnsibleModule(
        argument_spec=dict(
            captain_url=dict(required=True, type='str'),
            shc_peers=dict(required=True, type='list'),
            spl_user=dict(required=True, type='str'),
            spl_pass=dict(required=True, type='str'),
            retry_times=dict(required=True, type='int')
        )
    )
    shc_ready = ShcReady(module).run()
    res = dict(changed=False, ansible_facts=shc_ready)
    module.exit_json(**res)

if __name__ == '__main__':
    main()