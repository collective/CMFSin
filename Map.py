import ZODB
from ZODB.PersistentMapping import PersistentMapping
from OFS.SimpleItem import SimpleItem
from OrderPolicy import defaultPolicy, lookupPolicy, listPolicies, _policy

class Map(SimpleItem):
    def __init__(self, id):
        self.id = id
        self.channels = PersistentMapping()
        self.policy = defaultPolicy

    def setPolicy(self, name):
        self.policy = lookupPolicy(name, defaultPolicy)

    def setPriority(self, channel, pri):
        if not isinstance(channel, Channel):
            id = channel.id
        else:
            id = channel

        channel = self.channels[id]
        channel['priority'] = int(pri)


    def addChannel(self, channel, **kwargs):
        enabled  = kwargs.get('enabled', 1)
        priority = kwargs.get('priority', 0)

        self.channels[channel.id] = {'channel' : channel,
                                     'enabled' : enabled,
                                     'priority': priority,
                                     }
    def Channels(self):
        return self.channels.values()






