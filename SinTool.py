import os, os.path
import re
import locale
from types import StringType, UnicodeType

from AccessControl import ClassSecurityInfo
from BTrees.OOBTree import OOBTree
from SinConfigParser import ConfigParser
from Globals import InitializeClass, package_home
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.Expression import Expression
try:
    from Products.CMFCore.permissions import ManagePortal, ModifyPortalContent, View
except ImportError:
    from Products.CMFCore.CMFCorePermissions  import ManagePortal, ModifyPortalContent, View
    
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from StringIO import StringIO
from Acquisition import aq_base
from ComputedAttribute import ComputedAttribute
from zLOG import LOG, DEBUG, INFO

from Map import Map
from Channel import Channel
from rssparser import parse
from OrderPolicy import listPolicies, SimplePolicy
from Channel import TIME_KEY

from AccessControl import allow_class

schedRe = re.compile("(?P<freq>\d+)(?P<period>h|d|w|m|y):")

_parsers = {}

def registerParser(channel, parser):
    _parsers[channel] = parser

def lookupParser(channel, default=parse):
    return _parsers.get(channel, default)

def udecode(data, encoding='ascii'):
    if (encoding and encoding.lower() == 'unicode'
        or isinstance(data, UnicodeType)):
        return unicode(data)
    encodings = [encoding, 'utf-8']
    try:
        encodings.append(locale.nl_langinfo(locale.CODESET))
    except:
        pass
    try:
        encodings.append(locale.getlocale()[1])
    except:
        pass
    try:
        encodings.append(locale.getdefaultlocale()[1])
    except:
        pass
    encodings.append('latin-1')
    for enc in encodings:
        if not enc:
            continue
        try:
            return unicode(data, enc)
        except (UnicodeError, LookupError):
            pass
    raise UnicodeError(
        'Unable to decode input data.  Tried the following encodings: %s.'
        % ', '.join([repr(enc) for enc in encodings if enc]))


class SinTool(UniqueObject, ActionProviderBase, SimpleItem):
    """ CMF Syndication Client  """

    id        = 'sin_tool'
    meta_type = 'CMFSin Syndication Tool'

    security = ClassSecurityInfo()

    _actions = [ActionInformation(
        id='newfeeds'
        , title='NewsFeeds'
        , action=Expression(text='string: ${portal_url}/sin_tool/sincfg')
        , condition=Expression(text='member')
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
        self._v_data     = OOBTree()
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

    def encode(self, parsed_data):
        # Get site encoding

        enc = 'iso8859-1'
        try:
            pp = getToolByName(self, 'portal_properties')
            enc = getattr(pp.site_properties, 'default_charset', 'iso8859-1')
        except (AttributeError, KeyError):
            pass
        info = parsed_data['channel']
        data = parsed_data['items']

#         encoding = parsed_data.get('encoding', 'ascii')
#         for key in ('description', 'tagline', 'title'):
#             if isinstance(info[key], basestring) and not isinstance(info[key], unicode):
#                 info[key] = udecode(info[key], encoding)
#         for r in data:
#             for key in ('description', 'source', 'summary', 'title'):
#                 if isinstance(r[key], basestring) and not isinstance(r[key], unicode):
#                     r[key] = udecode(r[key], encoding)
#         return info, data
        
        if info.has_key('title'):
            if type(info['title']) not in (UnicodeType, ):
                info['title'] = udecode(info['title']).encode(enc)
        if info.has_key('description'):
            if type(info['description']) not in (UnicodeType, ):
                info['description'] = udecode(info['description']).encode(enc)
        for r in data:
            if r.has_key('title'):
                if type(r['title']) not in (UnicodeType, ):
                    r['title'] = udecode(r['title']).encode(enc)
        return info, data

    def _update(self, channel, force=None):
        # Hard update of a channels feed -> data
        try:
            parser = lookupParser(channel.id)
            data = self.encode(parser(channel.uri))
            channel.update(data, force)
            # Lastly, we update the existing data
            # if everything worked
            if not hasattr(aq_base(self), '_v_data'):
                self._v_data = OOBTree()
            self._v_data[channel.id] = data
        except (IOError, OSError):
            channel.failed()

    security.declareProtected(View, 'updateChannel')
    def updateChannel(self, channel, force=None):
        if not isinstance(channel, Channel):
            channel = self.channels[channel]

        if force or channel.requireUpdate():
            self._update(channel, force)

    security.declareProtected(View, 'sin')
    def sin(self, map_name, force=0, max_size=None):
        """
        Returns the syndication info for a given mapping
        force    -- force a channel update
        max_size -- max size of result set (may be used in policy to calc pri)
        """
        if map_name=='': return []

        if not hasattr(aq_base(self), '_v_data'):
            self._v_data = OOBTree()

        # Make sure map_name is a valid map name
        if map_name in self.maps.keys():
            map = self.maps.get(map_name)
            channels = map.Channels()
        else:
            # Otherwise see if it is a channel name. Construct appropriate objects.
            if map_name in self.channels.keys():
                map = self.channels[map_name]
                map.policy = SimplePolicy()
                channel = {}
                channel['priority'] = 0
                channel['enabled'] = 1
                channel['channel'] = map
                channels = (channel, )
            # Well, nothing we can use: return
            else:
                LOG('SinTool.sin', INFO, 'channel %s not found' % map_name)
                return []

        for ci in channels:
            enabled = ci['enabled']
            if not enabled: continue
            channel = ci['channel']
            self.updateChannel(channel, force)

# How safe is it to use threading inside Zope?
#             import threading
#             thread_name = "SinTool.Channel.%s" % channel.id
#             if not [t for t in threading.enumerate() if \
#                     t.getName() == thread_name]:
#                 threading.Thread(target=self.updateChannel, name=thread_name, \
#                                  args=(channel, force)).start()

        #Collect all the data for all the enabled channels now
        results = []
        links   = {}

        for ci in channels:
            enabled = ci['enabled']
            if not enabled: continue
            channel = ci['channel']
            priority = ci['priority']
            data = self._v_data.get(channel.id, None)
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
        name = os.path.join(package_home(globals()), \
                            os.path.basename(filename))
        if not name.endswith('.cfg'):
            name += '.cfg'

        fp = open(name)
        self.parse(fp)

    security.declarePrivate('save')
    def save(self, filename):
        """ Write config into a file """
        name = os.path.join(package_home(globals()), \
                            os.path.basename(filename))
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
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/sincfg?portal_status_message=Config+Updated")

    security.declareProtected(ManagePortal, 'manage_configSin')
    def manage_configSin(self, submit, config='', filename='', \
                         REQUEST=None, **kwargs):
        """config this puppy"""
        if submit == "Set Config":
            self.parse(config)
        elif submit == "Import":
            self.load(filename)
        elif submit == "Export":
            self.save(filename)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/manage_workspace")

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
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/manage_workspace")

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

    security.declareProtected(View, 'getChannelUri')
    def getChannelUri(self, map_name):
        """ return the uri of a given channel """
        map = self.sin_tool.maps.get(map_name)
        return map.Channels()[0]['channel'].uri    
        
    # slightly improved hack-o-rama to allow
    # using a simpler path expression: here/sintool/macros/slashdot
    security.declareProtected(View, 'macros')
    def macros(self):
        """ Allow traversing to map macro via ZPT """
        return SinMacro(self)

    macros = ComputedAttribute(macros, 1)


    ######## methods for the portal config interface ######

    security.declareProtected(ManagePortal, 'manage_edit_sincfg')
    def manage_edit_sincfg(self, REQUEST=None):
        """
            This method parses the user's input and generates the config file for the CMF SinTool.
        """
        if not REQUEST:
            return
        cfg = StringIO()
        # this list is needed to keep track of all valid channels - used while handling maps
        existing_channels = []
        
        cfg.write('[channels]\n')
        # Existing channels (Edit)
        for chan_name in REQUEST.get('chan_name', []):
            # write all existing channels to the config, unless they are marked to be deleted
            if not REQUEST.get('%s_delete' %chan_name, ''):
                cfg.write('%s = ' %chan_name)
                freq = REQUEST.get('%s_frequency' %chan_name, '1')
                if freq.strip()=='': freq = '1'
                cfg.write(freq)
                period = REQUEST.get('%s_period' %chan_name, 'd')
                cfg.write(period)
                url = REQUEST.get('%s_url' %chan_name, '')
                cfg.write(':%s\n' %url)
                existing_channels.append(chan_name)

        # New channel
        chan_name_new = REQUEST.get('chan_name_new', '')
        chan_url_new = REQUEST.get('chan_url_new', '')
        # If information for a new channel was entered, write it to the config
        if chan_name_new and chan_url_new:
            cfg.write('%s = ' % chan_name_new)
            freq = REQUEST.get('chan_frequency_new', '1')
            if freq.strip()=='': freq = '1'
            cfg.write(freq)
            period = REQUEST.get('chan_period_new', 'd')
            cfg.write(period)
            cfg.write(':%s\n' %chan_url_new)
            existing_channels.append(chan_name_new)

        # Existing maps (Edit)
        cfg.write('\n[maps]\n')
        for map_name in REQUEST.get('map_name', []):
            # write all existing maps to the config, unless they are are marked to be deleted
            if not REQUEST.get('%s_delete' %map_name, ''):
                channels = REQUEST.get('%s_channels' %map_name, [])
                if type(channels) in (StringType, UnicodeType):
                    channels = [channels]
                if len(channels) > 0:
                    # Filter out deleted channels
                    channels = filter(lambda x: x in existing_channels, channels)
                    # If there are no channels left, don't write the map
                    if len(channels) >0:
                        cfg.write('%s = ' %map_name)
                        policy = REQUEST.get('%s_policy' %map_name, 'simple')
                        cfg.write('%s:' %policy)
                        cfg.write('%s\n' %', '.join(channels))

        # New Map
        map_name_new = REQUEST.get('map_name_new', '')
        map_channels_new = REQUEST.get('map_channels_new', [])
        if type(map_channels_new)in (StringType, UnicodeType):
            map_channels_new = [map_channels_new]
        # If information for a new map was entered, write it to the config
        if map_name_new and len(map_channels_new) > 0:
            cfg.write('%s = ' %map_name_new)
            policy = REQUEST.get('map_policy_new', 'simple')
            cfg.write('%s:' %policy)
            cfg.write('%s\n' %', '.join(map_channels_new))

        config_value = cfg.getvalue()
        self.updateConfig(config_value)


    security.declarePublic('getSinChannels')
    def getSinChannels(self, cfg=None):
        """
            Convenience method that returns all channels from the config as a list of mappings
            Code taken from the parse() method
        """
        if not cfg:
            cfg = getattr(self, 'config', '')
        if type(cfg) in (StringType, UnicodeType):
            cfg = StringIO(cfg)
        config = ConfigParser()
        config.readfp(cfg)

        s = 'channels'
        options = config.options(s)
        channels = []
        for o in options:
            uri =  config.get(s, o, raw=1)
            period = 'd'
            frequency = '1'
            match = schedRe.match(uri)
            if match:
                uri = uri[match.end():]
                period = match.group('period')
                frequency = int(match.group('freq'))
            channels.append({'name': o, 'url': uri, 'period': period, 'frequency': frequency})

        return channels

    security.declarePublic('getSinMaps')
    def getSinMaps(self):
        """
            Convenience method that returns all maps from the config as a list of mappings
            Code taken from the parse() method
        """
        sin_tool = getToolByName(self, 'sin_tool')
        cfg = getattr(sin_tool, 'config', '')
        cfg = StringIO(cfg)
        config = ConfigParser()
        config.readfp(cfg)

        s = 'maps'
        maps = []
        options = config.options(s)
        for o in options:
            channels = config.get(s, o, raw=1)
            #We look for policy_name:x,y,z
            #if no policy is specified default is used
            idx = channels.find(':')
            policy = None
            if idx != -1:
                policy, channels = channels[:idx], channels[idx+1:]
            channels = channels.split(',')
            chans = []
            for c in channels:
                c = c.strip()  # remove whitespace around delimitters
                if c.endswith(')'):
                    #look for channel(pri) format
                    idx = c.rfind('(')
                    if idx != -1:
                        c = c[:idx]
                chans.append(c)
            maps.append({'name':o, 'policy': policy, 'channels': chans})
        return maps


    security.declarePublic('getSinTimeKeys')
    def getSinTimeKeys(self):
        """
            Convenience method that returns the TIME_KEY mapping from Channel
        """
        return TIME_KEY


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
               (id(self), self._template, self._macro, \
                ','.join(self._sintool.maps.keys()))

#
#     --> useless method ???
#
#     def __getattr__(self, key):
#         if key in self.__dict__.keys():
#             return getattr(self, key)
#         return getattr(self._sintool, key)

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


allow_class(SinMacro)