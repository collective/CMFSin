CMFSin Overview

 This is a simple syndication client for CMF. It uses rssparser and
shares many things in common with CMFNewsFeed but has a different
model for handling channels. It is designed to map _n_ channels or
feeds to sets of composite virtual channels which can then be called
in in a timely fashion. Most of the remaining work has to happen in UI
land.

CMFSin now should work in Plone 2.0, 2.1, and 2.5.  Please report any 
bugs to the issue tracker: http://plone.org/products/cmfsin/issues

 <b>Step-by-step instructions</b>

 1. Install using the CMFQuickInstaller or the Plone Control Panel.

    In the ZMI, add a CMFQuickInstaller Tool to your CMF/Plone Site.
    Click on portal_quickinstaller.  Check CMFSin and click "Install".

 2. In the ZMI, go to the new sin_tool object of your CMF/Plone site.
    Add RSS or RDF channels to the "channels" section:

      syntax: <channelname>=<url>

      ex: freshmeat=http://freshmeat.net/backend/fm-releases-software.rdf

 3. Add syndication mappings to the "map" section.

      syntax: <mapname>=<channelname> [,<channelname>]*

      ex: geek=freshmeat,slashdot

 4. Click "Set Config".

 5. Finally, go to the Properties tab of your CMF/Plone site then
    add the mappings you defined to your left_slots or right_slots.

      syntax: here/sin_tool/macros/<mapname>

      ex: here/sin_tool/macros/geeknews

Credits:

 * Ben <bcsaller@yahoo.com>

 * Thanks to Mark Pilgrim for the rssparser that I use (a hacked up version of)

 * Andy McKay, Richard Amerman and Jon Lim and Sprint Victoria for 0.6

 * Sidnei da Silva (dreamcatcher) for house cleaning and beer drinking.
 
 * Portland Plone User Group for cutting a new release after more than 2 years of
 dormancy!
 