import os, os.path
import re

from AccessControl import ClassSecurityInfo
from BTrees.OOBTree import OOBTree
from SinConfigParser import ConfigParser
from Globals import InitializeClass, package_home
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.Expression import Expression
from Products.CMFCore.CMFCorePermissions  import ManagePortal, ModifyPortalContent, View
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from StringIO import StringIO
from ComputedAttribute import ComputedAttribute

from Map import Map
from Channel import Channel
from rssparser import parse
from OrderPolicy import listPolicies

schedRe = re.compile("(?P<freq>\d+)(?P<period>h|d|w|m|y):")

_parsers = {}

def registerParser(channel, parser):
    _parsers[channel] = parser

def lookupParser(channel, default=parse):
    return _parsers.get(channel, default)

class SinTool(UniqueObject, ActionProviderBase, SimpleItem):
    """ CMF Syndication Client  """

    id        = 'sin_tool'
    meta_type = 'CMFSin Syndication Tool'

    security = ClassSecurityInfo()

    _actions = [ActionInformation(
        id='newfeeds'
        , title='NewsFeeds'
        , action=Expression(
        text='string: ${portal_url}/sin_tool/sincfg')
        ,condition=Expression(
        text='member')
#        , permissions=(ManageNewsFeeds,)
        , permissions=(ManagePortal,)
        , category='portal_tabs'
        , visible=0
        )]

    manage_options=(
        ({ 'label'   : 'Config',
           'action'  : 'manage_configForm',
           },
         {  'label'  : 'Debug',
            'action' : 'manage_debugForm',
            },
         ) + SimpleItem.manage_options
        +  ActionProviderBase.manage_options
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

    security.declarePublic('Maps')
    def Maps(self):
        """ Available Maps """
        return self.maps.values()

    security.declarePublic('Channels')
    def Channels(self):
        """ Available Channels """
        return self.channels.values()

    security.declarePublic('Policies')
    def Policies(self):
        """ Available Policies """
        return listPolicies()

    def _update(self, channel):
        # Hard update of a channels feed -> data
        try:
            parser = lookupParser(channel.id)
            data = parser(channel.uri)
            channel.update(data)
            # Lastly, we update the existing data
            # if everything worked
            self.data[channel.id] = data
        except (IOError, OSError):
            channel.failed()

    security.declareProtected(View, 'updateChannel')
    def updateChannel(self, channel, force=0):
        if not isinstance(channel, Channel):
            channel = self.channels[channel]

        if force == 1 or channel.requireUpdate():
            self._update(channel)

    security.declareProtected(View, 'sin')
    def sin(self, map, force=0, max_size=None):
        """
        Returns the syndication info for a given mapping
        force    -- force a channel update
        max_size -- max size of result set (may be used in policy to calc pri)
        """

        # With a fallback to channel for development
        map = self.maps.get(map)
        if not map: map = self.channels[map]

        for ci in map.Channels():
            enabled = ci['enabled']
            if not enabled: continue
            channel = ci['channel']
            self.updateChannel(channel, force)

        #Collect all the data for all the enabled channels now
        results = []
        links   = {}

        for ci in map.Channels():
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

    security.declareProtected(ModifyPortalContent, 'addChannel')
    def addChannel(self, name, url, **kwargs):
        c = Channel(name, url, **kwargs)
        self.channels[name] = c

    security.declareProtected(ModifyPortalContent, 'addMap')
    def addMap(self, map, channels=[]):
        self.maps[map] = m = Map(map)
        for c in channels:
            c = self.channels[c]
            m.addChannel(c)
        return m

    security.declarePrivate('parse')
    def parse(self, file):
        if type(file) == type(''):
            file = StringIO(file)

        config = ConfigParser()
        config.readfp(file)

        s = 'channels'
        options = config.options(s)
        args = {}
        for o in options:
            uri =  config.get(s, o, raw=1)
            match = schedRe.match(uri)
            if match:
                uri = uri[match.end():]
                args['period']    = match.group('period')
                args['frequency'] = int(match.group('freq'))
            self.addChannel(o, uri, **args)
            args.clear()

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
                c = c.strip()  # remove whitespace around delimitters
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

    security.declarePrivate('load')
    def load(self, filename):
        """ Load a file into config """
        name = os.path.join(package_home(globals()), os.path.basename(filename))
        if not name.endswith('.cfg'):
            name += '.cfg'

        fp = open(name)
        self.parse(fp)

    security.declarePrivate('save')
    def save(self, filename):
        """ Write config into a file """
        name = os.path.join(package_home(globals()), os.path.basename(filename))
        if not name.endswith('.cfg'):
            name += '.cfg'

        fp = open(name, 'w')
        fp.write(self.config)
        fp.close()

    security.declareProtected(ModifyPortalContent, 'updateConfig')
    def updateConfig(self, config=None, REQUEST=None, *args):
        """Update the config using new info"""
        self.parse(config)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/sincfg?portal_status_message=Config+Updated")

    security.declareProtected(ManagePortal, 'manage_configSin')
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

    security.declareProtected(ManagePortal, 'manage_debug')
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

    security.declarePrivate('setCurrentFeed')
    def setCurrentFeed(self, name):
        self._v_current_feed = name

    security.declareProtected(View, 'getCurrentFeed')
    def getCurrentFeed(self):
        """ Get the current configured feed """
        fd = self._v_current_feed
        if fd not in self.maps.keys():
            raise ValueError, "'%s' is not a valid map" % fd
        return fd

    # slightly improved hack-o-rama to allow
    # using a simpler path expression: here/sintool/macros/slashdot
    security.declareProtected(View, 'map')
    def macros(self):
        """ Allow traversing to map macro via ZPT """
        return SinMacro(self)

    macros = ComputedAttribute(macros, 1)

InitializeClass(SinTool)

class SinMacro:
    """ A dict-like object to allow configurable traversing to the macro
    while setting up the current feed reliably """

    def __init__(self, sintool, template='sinBox', macro='sinBox'):
        self._sintool = sintool
        self._template = template
        self._macro = macro

    def __repr__(self):
        return '<SinMacro at %s template: %s, macro: %s, maps: %s>' % \
               (id(self), self._template, self._macro, ','.join(self._sintool.maps.keys()))

    def __getattr__(self, key):
        if key in self.__dict__.keys():
            return getattr(self, key)
        return getattr(self._sintool, key)

    def __getitem__(self, key):
        if key not in self._sintool.maps.keys():
            raise KeyError(key)
        skinstool = getToolByName(self._sintool, 'portal_skins')
        template = getattr(skinstool, self._template)
        macro = template.macros[self._macro]
        # this is a little bad, but here we dont have
        # request etc...
        self._sintool.setCurrentFeed(key)
        return macro


