/*
JavaScript definitions to handle comments on the site
*/

(function($) {
$(document).ready(function() {
    var SET_TIME = 5000;
    var $COMMENT_FLAG_MODAL = $('#spc-comment-flag-modal');

    // flag comment
    $('body').on('click', '.spc-comment-flag', function() {
        $COMMENT_FLAG_MODAL.data('comment-id', $(this).data('id'));
    });

    $COMMENT_FLAG_MODAL.on('click', "button[data-submit='flag']", function() {
        var comment_id = $COMMENT_FLAG_MODAL.data('comment-id');
        var $comment_element = $('#c' + comment_id);
        var $success_resp = $comment_element.find("[data-resp='success'][data-action='flag']");
        var $error_resp = $comment_element.find("[data-resp='error'][data-action='flag']");
        var $server_error_resp = $comment_element.find("[data-resp='server-error'][data-action='flag']");

        $.ajax({
            type: 'post',
            url: '/comments/flag/' + comment_id + '/',
            data: {},
            success: function(data) {
                if (data.success) {
                    $comment_element.find('.spc-comment-flag').parent().hide();
                    $success_resp.show();
                } else {
                    $error_resp.stop(true, true).show().fadeOut(SET_TIME);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $server_error_resp.stop(true, true).show().fadeOut(SET_TIME);
            }
        });
        $COMMENT_FLAG_MODAL.modal('hide');
    });

});
})(window.jQuery);
