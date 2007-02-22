from Products.CMFSin import sin_globals
from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import addDirectoryViews

SKIN_NAME = "sin"
_globals = globals()
STYLESHEETS = (
    {'id': 'sin.css', 'media': 'screen', 'rendering': 'import'},
        )

def install_tools(self, out):
    if not hasattr(self, "sin_tool"):
        addTool = self.manage_addProduct['CMFSin'].manage_addTool
        addTool('CMFSin Syndication Tool')

def install_actions(self, out):
    at = getToolByName(self, "portal_actions")
    at.manage_aproviders('sin_tool', add_provider=1)

def install_subskin(self, out, skin_name=SKIN_NAME, globals=sin_globals):
    skinstool=getToolByName(self, 'portal_skins')
    if skin_name not in skinstool.objectIds():
        addDirectoryViews(skinstool, 'skins', globals)

    for skinName in skinstool.getSkinSelections():
        path = skinstool.getSkinPath(skinName)
        path = [i.strip() for i in  path.split(',')]
        try:
            if skin_name not in path:
                path.insert(path.index('custom') +1, skin_name)
        except ValueError:
            if skin_name not in path:
                path.append(skin_name)

        path = ','.join(path)
        skinstool.addSkinSelection( skinName, path)

        
def registerStylesheets(self, out, stylesheets):
    # register additional CSS stylesheets with portal_css
    csstool = getToolByName(self, 'portal_css')
    existing = csstool.getResourceIds()
    updates = []
    for css in stylesheets:
        if not css.get('id') in existing:
            csstool.registerStylesheet(**css)
        else:
            updates.append(css)
    if updates:
        updateResources(csstool, updates)
    print >> out, "installed the Plone additional stylesheets."

        
def install(self):
    out = StringIO()
    print >>out, "Installing CMFSin"

    install_tools(self, out)
    install_actions(self, out)
    install_subskin(self, out)
    registerStylesheets(self, out, STYLESHEETS)
    self.sin_tool.load('default.cfg')
    return out.getvalue()


def uninstall(self):
    at = getToolByName(self, "portal_actions")
    at.deleteActionProvider('sin_tool')

