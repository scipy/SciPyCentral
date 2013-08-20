/*
JavaScript definitions to handle comments on the site
*/

(function($) {
$(document).ready(function() {
    var SET_TIME = 5000;
    var $COMMENT_FLAG_MODAL = $('#spc-comment-flag-modal');
    var $COMMENT_DEL_MODAL = $('#spc-comment-delete-modal');
    var $COMMENT_EDIT_MODAL = $('#spc-comment-edit-modal');

    var $POST_COMMENT = $('#spc-post-comment');
    var $COMMENT_PREVIEW = $POST_COMMENT.find("[data-resp='success'][data-action='preview']");
    var $COMMENT_PREVIEW_ERR = $POST_COMMENT.find("[data-resp='error'][data-action='preview']");
    var $COMMENT_PREVIEW_SERVER_ERR = $POST_COMMENT.find("[data-resp='server-error'][data-action='preview']");

    var $POST_LOADING_IMAGE = $POST_COMMENT.find('.preview-image');
    var $POST_COMMENT_RESP = $POST_COMMENT.find("[data-resp='success'][data-action='comment']");
    var $POST_COMMENT_ERR = $POST_COMMENT.find("[data-resp='error'][data-action='comment']");
    var $POST_COMMENT_SERVER_ERR = $POST_COMMENT.find("[data-resp='server-error'][data-action='comment']");
    var $COMMENT_COUNT = $('#spc-comment-count');

    var $EDIT_LOADING_IMAGE = $COMMENT_EDIT_MODAL.find('.preview-image');
    var $COMMENT_EDIT_PREVIEW = $COMMENT_EDIT_MODAL.find("[data-resp='success'][data-action='preview']");
    var $COMMENT_EDIT_PREVIEW_ERR = $COMMENT_EDIT_MODAL.find("[data-resp='error'][data-action='preview']");
    var $COMMENT_EDIT_PREVIEW_SERVER_ERR = $COMMENT_EDIT_MODAL.find("[data-resp='server-error'][data-action='preview']");

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

    // preview comment
    $('body').on('click', '.spc-comment-preview', function() {
        var data_mode = $(this).data('mode');

        if (data_mode === 'new') {
            var comment = $('#id_comment').val();
            var $loading_image = $POST_LOADING_IMAGE;
            var $preview = $COMMENT_PREVIEW;
            var $preview_err = $COMMENT_PREVIEW_ERR;
            var $preview_server_err = $COMMENT_PREVIEW_SERVER_ERR;
        } else if (data_mode === 'edit') {
            var comment = $('#id_edit_comment').val();
            var $loading_image = $EDIT_LOADING_IMAGE;
            var $preview = $COMMENT_EDIT_PREVIEW;
            var $preview_err = $COMMENT_EDIT_PREVIEW_ERR;
            var $preview_server_err = $COMMENT_EDIT_PREVIEW_SERVER_ERR;
        }

        $loading_image.show();
        $preview.hide();
        $.ajax({
            type: 'get',
            url: '/comments/preview/',
            data: {'rest_comment': comment},
            success: function(response) {
                if (response.success) {
                    $loading_image.hide();
                    $preview.show().html(response.html_comment);
                    MathJax.Hub.Queue(['Typeset', MathJax.Hub, $preview.attr('id')]);
                } else {
                    $loading_image.hide();
                    $preview_err.stop(true, true).show().fadeOut(SET_TIME);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $loading_image.hide();
                $preview_server_err.stop(true, true).show().fadeOut(SET_TIME);
            }
        });

    });

    // post comment
    $POST_COMMENT.on('click', "[data-submit='post-comment']", function() {
        var $comment_form = $POST_COMMENT.find('form');
        var $submit_button = $POST_COMMENT.find("[data-submit='post-comment']");

        $comment_form.hide();
        $submit_button.hide();
        $COMMENT_PREVIEW.hide();
        $POST_LOADING_IMAGE.show();
        $.ajax({
            type: 'post',
            url: '/comments/post/',
            data: $comment_form.serialize(),
            success: function(response) {
                if (response.success) {
                    $('#spc-comment-list').load(' ' + '#spc-comment-list', function() {
                        MathJax.Hub.Queue(['Typeset', MathJax.Hub, 'spc-comment-list']);
                    });
                    $COMMENT_COUNT.html(response.comments_count);
                    $comment_form.trigger('reset');
                    $POST_LOADING_IMAGE.hide();
                    $POST_COMMENT.prev().find("li > a[href='#comment']").tab('show');
                    $comment_form.show();
                    $submit_button.show();
                    $COMMENT_PREVIEW.empty();
                    $('html,body').animate({scrollTop: $POST_COMMENT.offset().top}, 'slow');
                    $POST_COMMENT_RESP.stop(true, true).show().fadeOut(SET_TIME);
                } else {
                    $comment_form.show();
                    $submit_button.show();
                    $COMMENT_PREVIEW.show();
                    $POST_LOADING_IMAGE.hide();
                    $POST_COMMENT_ERR.stop(true, true).show().fadeOut(SET_TIME);
                }
                MathJax.Hub.Queue(['Typeset', MathJax.Hub]); // load math
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $POST_LOADING_IMAGE.hide();
                $COMMENT_PREVIEW.show();
                $comment_form.show();
                $submit_button.show();
                $POST_COMMENT_SERVER_ERR.stop(true, true).show().fadeOut(SET_TIME);
            }

        });
    });

    // delete comment
    $('body').on('click', '.spc-comment-delete', function() {
        $COMMENT_DEL_MODAL.data('comment-id', $(this).data('id'));
    });

    $COMMENT_DEL_MODAL.on('click', "button[data-submit='delete']", function() {
        var comment_id = $COMMENT_DEL_MODAL.data('comment-id');
        var $comment_element = $('#c' + comment_id);

        var $error_resp = $comment_element.find("[data-resp='error'][data-action='delete']");
        var $server_error_resp = $comment_element.find("[data-resp='server-error'][data-action='delete']");

        $.ajax({
            type: 'post',
            url: '/comments/user_delete/' + comment_id + '/',
            data: {},
            success: function(data) {
                if (data.success) {
                    var comment_count = parseInt($COMMENT_COUNT.text().trim(), 10);
                    $comment_element.remove();
                    $COMMENT_COUNT.html(comment_count - 1);
                } else {
                    $error_resp.stop(true, true).show().fadeOut(SET_TIME);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $server_error_resp.stop(true, true).show().fadeOut(SET_TIME);
            }
        });
        $COMMENT_DEL_MODAL.modal('hide');
    });


    // edit comment
    $('body').on('click', '.spc-comment-edit', function() {
        var $this = $(this);
        var $comment_element = $('#c' + $this.data('id'));
        var $rest_comment_text = $comment_element.find('.media-body > .rest-text');
        $('#id_edit_comment').val($rest_comment_text.text().trim());
        $COMMENT_EDIT_MODAL.data('comment-id', $this.data('id'));
        $('#edit-comment-tab a').tab('show');
    });

    $COMMENT_EDIT_MODAL.on('click', "button[data-submit='edit']", function() {
        var comment_id = $COMMENT_EDIT_MODAL.data('comment-id');
        var $comment_element = $('#c' + comment_id);
        var $html_comment_text = $comment_element.find('.media-body > .html-text');
        var $rest_comment_text = $comment_element.find('.media-body > .rest-text');

        var $success_resp = $comment_element.find("[data-resp='success'][data-action='edit']");
        var $error_resp = $comment_element.find("[data-resp='error'][data-action='edit']");
        var $server_error_resp = $comment_element.find("[data-resp='server-error'][data-action='edit']");

        var $edit_form = $COMMENT_EDIT_MODAL.find('form');

        $.ajax({
            type: 'post',
            url: '/comments/edit/' + comment_id + '/',
            data: $edit_form.serialize(),
            success: function(data) {
                if (data.success) {
                    $success_resp.stop(true, true).show().fadeOut(SET_TIME);
                    $html_comment_text.html(data.rest_comment);
                    $rest_comment_text.html($edit_form.find('#id_edit_comment').val().trim());
                    MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
                } else {
                    $error_resp.stop(true, true).show().fadeOut(SET_TIME);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $server_error_resp.stop(true, true).show().fadeOut(SET_TIME);
            }
        });
        $COMMENT_EDIT_MODAL.modal('hide');
    });

});
})(window.jQuery);
