from AccessControl import ClassSecurityInfo
from BTrees.OOBTree import OOBTree
from ConfigParser import ConfigParser
from Globals import InitializeClass, package_home
from OFS.SimpleItem import SimpleItem
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from StringIO import StringIO
import os, os.path

from Map import Map
from Channel import Channel
from rssparser import parse
from OrderPolicy import listPolicies

class SinTool(UniqueObject, ActionProviderBase, SimpleItem):
    """ CMF Syndication Client  """
    id        = 'sin_tool'
    meta_type = 'CMFSin Syndication Tool'
    

    manage_options=(
        ({ 'label'   : 'Config',
           'action'  : 'manage_configForm',
           },
         {  'label'  : 'Debug',
            'action' : 'manage_debugForm',
            },
         ) + SimpleItem.manage_options

        )

    manage_debugForm = PageTemplateFile('www/debug', globals())
    manage_configForm = PageTemplateFile('www/config', globals())

    def __init__(self):
        self._reset()
        
    def _reset(self, config=None):
        self.maps     = OOBTree()
        self.data     = OOBTree()
        self.channels = OOBTree()
        self.config   = config
        
    def Maps(self): return self.maps.values()
    def Channels(self): return self.channels.values()
    def Policies(self): return listPolicies()
    
    def _update(self, channel):
        # Hard update of a channels feed -> data
        try:
            data = parse(channel.uri)
            channel.update(data)
            # Lastly, we update the existing data
            # if everything worked
            self.data[channel.id] = data
        except (IOError, OSError):
            channel.failed()
        
    
    def updateChannel(self, channel, force=0):
        if not isinstance(channel, Channel):
            channel = self.channels[channel]

        if force == 1 or channel.requireUpdate():
            self._update(channel)

    def sin(self, map, force=0, max_size=None):
        """Returns the syndication info for a given mapping
        force    -- force a channel update
        max_size -- max size of result set (may be used in policy to calc pri)
        """
        # With a fallback to channel for development
        map = self.maps.get(map)
        if not map: map = self.channels[map]
            
        for ci  in map.Channels():
            enabled = ci['enabled']
            if not enabled: continue
            channel = ci['channel']
            self.updateChannel(channel, force)

        #Collect all the data for all the enabled channels now
        results = []
        links   = {}

        for ci  in map.Channels():
            enabled = ci['enabled']
            if not enabled: continue
            channel = ci['channel']
            priority = ci['priority']
            data = self.data.get(channel.id, None)
            final   = []

            if not data: continue
            # We remove dup links inline
            for link in data[1]:
                if not links.has_key(link['link']):
                    links[link['link']] = 1
                    final.append(link)
                #We don't cache skips now because the Map
                #doesn't keep any data, just the channel
                #relationship, if this is an issue
                #its easy enough to change
                
            data[0]['priority'] = priority
            results.append(data)
            
        policy = map.policy
        results = policy.order(results, max_size=max_size)

        return results


    def addChannel(self, name, url):
        c = Channel(name, url)
        self.channels[name] = c
        
    def addMap(self, map, channels=[]):
        self.maps[map] = m = Map(map)
        for c in channels:
            c = self.channels[c]
            m.addChannel(c)
        return m
    
    def parse(self, file):
        if type(file) == type(''):
            file = StringIO(file)

        config = ConfigParser()
        config.readfp(file)

        #self._reset()
        
        s = 'channels'
        options = config.options(s)
        for o in options:
            self.addChannel(o, config.get(s, o, raw=1))

        s = 'maps'
        options = config.options(s)
        for o in options:
            channels = config.get(s, o, raw=1)
            #We look for policy_name:x,y,z
            #if no policy is specified default is used
            idx = channels.find(':')
            policy = None
            if idx != -1:
                policy, channels = channels[:idx], channels[idx+1:]

            m = self.addMap(o)
            if policy:
                m.setPolicy(policy)

            channels = channels.split(',')
            for c in channels:
                if c.endswith(')'):
                    #look for channel(pri) format
                    idx = c.rfind('(')
                    if idx != -1:
                        pri = int(c[idx+1:-1])
                        c = c[:idx]
                else:
                    pri = 0
                    
                c = self.channels[c]
                m.addChannel(c, priority=pri)
                

        file.seek(0)
        self.config = file.read()
        
    def load(self, filename):
        #load a file into config
        name = os.path.join(package_home(globals()), os.path.basename(filename))
        if not name.endswith('.cfg'):
            name += '.cfg'

        fp = open(name)
        #self._reset()
        self.parse(fp)

        

    def save(self, filename):
        #load a file into config
        name = os.path.join(package_home(globals()), os.path.basename(filename))
        if not name.endswith('.cfg'):
            name += '.cfg'
            
        fp = open(name, 'w')
        fp.write(self.config)
        fp.close()
        
        
        
    def manage_configSin(self, submit, config='', filename='', REQUEST=None, **kwargs):
        """config this puppy"""
        if submit == "Set Config":
            self.parse(config)
        elif submit == "Import":
            self.load(filename)
        elif submit == "Export":
            self.save(filename)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_workspace")

    def manage_debug(self, submit, maps=(),  REQUEST=None, *args, **kwargs):
        """update maps for testing"""
        if submit == "Purge":
            self._reset(self.config)
            self.parse(self.config)
            
        elif submit == "Update Maps":
            for id in maps:
                self.sin(id, force=1)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_workspace")


InitializeClass(SinTool)




