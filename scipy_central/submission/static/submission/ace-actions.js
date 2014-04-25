/* 
    JavaScript settings to handle ACE Editor
*/

(function($) {
$(document).ready(function() {

    $('[data-editor]').each(function() {
        var $textbox = $(this);
        var text_val = '';
        if ($textbox.is('textarea')) {
            text_val = $textbox.val();
        } else if ($textbox.is('div')) {
            text_val = $textbox.html();
        }

        var mode = $textbox.data('editor');
        var is_readonly = false;
        if ($textbox.data('readonly') === true) {
            is_readonly = true;
        }

        var edit_div = $('<div>', {
            'tabindex': $textbox.attr('tabindex'),
            'class': 'ace-editor'
        }).insertBefore($textbox);

        $textbox.css('visibility', 'hidden');
        $textbox.removeAttr('tabindex');

        var editor = ace.edit(edit_div[0]);
        editor.setReadOnly(is_readonly);
        editor.setTheme('ace/theme/github');
        editor.getSession().setMode('ace/mode/' + mode);
        editor.getSession().setValue(text_val);

        editor.getSession().on('change', function() {
            if($textbox.is('textarea')) {
                $textbox.val(editor.getSession().getValue());
            } 
        });
    });
});
})(window.jQuery);
