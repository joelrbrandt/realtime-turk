from mod_python import apache, util
from mako.template import Template
from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException

mylookup = TemplateLookup(directories=['/var/www/realtime'],
                          module_directory='/tmp/mako_modules',
                          output_encoding='utf-8',
                          encoding_errors='replace')

def serve_template(request, **kwargs):
    mytemplate = mylookup.get_template(request.uri)
    request.write(mytemplate.render(**kwargs))

def handler(request):
    request.content_type = "text/html"
    try:
        serve_template(request, fieldstorage=util.FieldStorage(request))
    except TopLevelLookupException:
        return apache.HTTP_NOT_FOUND
    #except:
    #    return apache.HTTP_INTERNAL_SERVER_ERROR

    return apache.OK
