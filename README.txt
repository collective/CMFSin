CMFSin Overview

 This is a simple syndication client for CMF. It uses rssparser and
shares many things in common with CMFNewsFeed but has a different
model for handling channels. It is designed to map _n_ channels or
feeds to sets of composite virtual channels which can then be called
in in a timely fashion. Most of the remaining work has to happen in UI
land.

 <b>Step-by-step instructions</b>

 1. Install either using the CMFQuickInstaller or using an external
    method.

    Using CMFQuickInstaller:

    In the ZMI, add a CMFQuickInstaller Tool to your CMF/Plone Site.
    Click on portal_quickinstaller.  Check CMFSin and click "Install".
	 
    Using External Method:

    Add an External Method to your CMF/Plone site and specify the
    following:

      ID: install_cmfsin

      Module Name: CMFSin.Install

      Function Name: install

    Click "Test" to install CMFSin.

 2. In the ZMI, go to the new sin_tool object of your CMF/Plone site.
    Add RSS or RDF channels to the "channels" section:

      syntax: <i>channelname</i>=<i>url</i>

      ex: freshmeat=http://freshmeat.net/backend/fm-releases-software.rdf

 3. Add syndication mappings to the "map" section.

      syntax: <i>mapname</i>=<i>channelname</i> [,<i>channelname</i>]*
 
      ex: geek=freshmeat,slashdot

 4. Click "Set Config".
    
 5. Finally, go to the Properties tab of your CMF/Plone site then 
    add the mappings you defined to your left_slots or right_slots. 

      syntax: here/sin_tool/map_<i>mapname</i>

      ex: here/sin_tool/map_geek


 <b>Older Documentation</b>

 See default.cfg for more information on configuring the mappings. The file www/debug.zpt shows how you might call the SinTool.sin(mapName) method to display syndication data. 

 To install just add the SinTool to your CMF Site. If you want to get
running quickly and to see if its working just goto the config tab and
in the box at the bottom type "test", then hit import. After that try
the "debug" tab.

 CMFSin ships with a sample usage of the sinBox slot.

 To add an rss slot to your main template, go to your portal's properties  (not your portal_properties!) in the zmi, and add 'here/rss_slot/macros/humorBox' to either the left_slots or right_slots.

   Good Luck,
   -Ben <bcsaller@yahoo.com>

 PS: Thanks to Mark Pilgrim for the rssparser that I use (a hacked up version of) 
