
This is a simple syndication client for CMF. It uses rssparser and
shares many things in common with CMFNewsFeed but has a different
model for handling channels. It is designed to map _n_ channels or
feeds to sets of composite virtual channels which can then be called
in in a timely fashion. Most of the remaining work has to happen in UI
land.

See docs/config.txt to get started. The file www/debug.zpt shows how
you might call the SinTool.sin(mapName) method to display syndication
data. 

To install just add the SinTool to your CMF Site. If you want to get
running quickly and to see if its working just goto the config tab and
in the box at the bottom type "test", then hit import. After that try
the "debug" tab.

CMFSin ships with a sample usage of the sinBox slot.

To add an rss slot to your main template, go to your portal's properties 
(not your portal_properties!) in the zmi, and add 'here/rss_slot/macros/humorBox'
to either the left_slots or right_slots.


    Good Luck,
     -Ben <bcsaller@yahoo.com>

PS: Thanks to Mark Pilgrim for the rssparser that I use (a hacked up version of) 
