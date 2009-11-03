from Products.CMFCore.DirectoryView import registerDirectory
import Products.CMFCore.utils

ADD_CONTENT_PREMISSIONS = 'Manage Portal'
sin_globals = globals()
registerDirectory('skins', sin_globals)

PKG_NAME = "CMFSin"

from Products.CMFSin.SinTool import SinTool
tools = (SinTool, )


def initialize(context):
    Products.CMFCore.utils.ToolInit(PKG_NAME + " Tool", tools=tools,
                   icon="tool.gif",
                   ).initialize(context)

types_globals=globals()
