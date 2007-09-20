## Script (Python) "cmfsincfg_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=edit the config file of the sin_tool (CMFSin)
##
request = context.REQUEST
from zLOG import LOG, INFO

status = 'success'
mesg = 'Editing ok'

try:
    context.manage_edit_sincfg(request)
    status = "success"
except Exception, e:
    status = "failure"
    mesg = "An error occured. Editing was not possible."
    LOG('SinTool.cmfsincfg_edit', INFO, 'editing not possible: %s' %e)

return state.set(status=status, context=context, portal_status_message=mesg)
