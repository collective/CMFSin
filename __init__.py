from AccessControl import ModuleSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.DirectoryView import registerDirectory
import Products.CMFCore.utils

ADD_CONTENT_PREMISSIONS = 'Manage Portal'
registerDirectory('skins', globals())

PKG_NAME = "CMFSin"

###
## tools
###
from Products.CMFSin.SinTool import SinTool
tools = (
    SinTool,
    )


def initialize(context):
    Products.CMFCore.utils.ToolInit(PKG_NAME + " Tool", tools=tools,
                   product_name=PKG_NAME,
                   icon="tool.gif",
                   ).initialize(context)


types_globals=globals()
