from django.conf import settings
from datetime import datetime

def global_template_variables(request):
    return {'JQUERY_URL': settings.JQUERY_URL,
             'JQUERYUI_URL': settings.JQUERYUI_URL,
             'JQUERYUI_CSS': settings.JQUERYUI_CSS,
             'ANALYTICS_SNIPPET': settings.ANALYTICS_SNIPPET,
             'THE_YEAR': str(datetime.now().year),
             # Assume the submitting user is not validated, by default
             'validated_user': False,

             # Inc
             'TAGGING_JAVSCRIPT': """
<script>
<!--JQuery example: http://jqueryui.com/demos/autocomplete/#multiple-remote -->
$(function() {
    function split( val ) {
        return val.split( /,\s*/ );
    }
    function extractLast( term ) {
        return split( term ).pop();
    }

    $("#id_sub_tags")
        // don't navigate away from the field on tab when selecting an item
        .bind( "keydown", function( event ) {
            if ( event.keyCode === $.ui.keyCode.TAB &&
                    $( this ).data( "autocomplete" ).menu.active ) {
                event.preventDefault();
            }
        })
        .autocomplete({
            source: function( request, response ) {
                $.getJSON( "/item/tag_autocomplete", {
                    term: extractLast( request.term )
                }, response );
            },
            search: function() {
                // custom minLength
                var term = extractLast( this.value );
                if ( term.length < 1 ) {
                    return false;
                }
            },
            focus: function() {
                // prevent value inserted on focus
                return false;
            },
            select: function( event, ui ) {
                var terms = split( this.value );
                // remove the current input
                terms.pop();
                // add the selected item
                terms.push( ui.item.value );
                // add placeholder to get the comma-and-space at the end
                terms.push( "" );
                this.value = terms.join( ", " );
                return false;
            }
        });
});
</script>
"""
            }