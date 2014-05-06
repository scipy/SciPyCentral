/*
    JavaScript for reST
*/

(function($) {
$(document).ready(function() {

    var SET_TIME = 6000;

    $('[data-preview]').on('click', function() {

        $this = $(this);

        var $content =  $('#' + $this.data('pcontent'));
        var $preview = $('#' + $this.data('presponse'));

        var content_value = '';
        if ($content.is('textarea')) {
            content_value = $content.val();
        } else if ($content.is('div')) {
            content_value = $content.html();
        }

        var $loading = $preview.parent().find('.preview-image');
        var $error = $preview.parent().find("[data-resp='error']");
        var $server_error = $preview.parent().find("[data-resp='server-error']");

        $preview.empty().hide();
        $loading.show();

        $.ajax({
            type: 'get',
            url: '/rest/',
            data: {
                'rest_text': content_value,
                'source': $this.data('preview')
            },
            success: function(data) {
                if (data.success) {
                    $preview.html(data.html_text).show();
                    MathJax.Hub.Queue(['Typeset', MathJax.Hub, $preview.attr('id')]);
                } else {
                    $error.stop(true, true).show().fadeOut(SET_TIME);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $server_error.stop(true, true).show().fadeOut(SET_TIME);
            }
        }).always(function() {
            $loading.hide();
        });
    });
});
})(window.jQuery);
