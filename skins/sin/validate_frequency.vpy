## Controller Python Script "validate_frequency"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=validates frequency settings (checks for valid integer)

request = context.REQUEST

fieldnames = []
for chan_name in request.get('chan_name', []):
    fieldnames.append('%s_frequency' %chan_name)
fieldnames.append('chan_frequency_new')

for fieldname in fieldnames:
    frequency = request.get(fieldname, '')
    try:
        int(frequency)
    except:
        state.setError(fieldname, 'Please supply a valid integer')

if state.getErrors():
    return state.set(status='failure', portal_status_message='Please correct the indicated errors.')

return state