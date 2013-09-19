$('body').on('click', function (e) {
    $('.spc-popover').each(function () {
        //the 'is' for buttons that triggers popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            $(this).popover('hide');
        }
    });
});
