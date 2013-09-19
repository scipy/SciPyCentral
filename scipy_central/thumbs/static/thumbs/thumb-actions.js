/*
JavaScript definitons to handle reputation system on site
*/

(function($) {
$(document).ready(function() {

    var $SPC_POPOVER = $('.spc-popover');

    function show_vote(thumb_as, thumb_for, target, other, vote_count) {
        var fact = -1;
        if (thumb_as === 'up')
            fact = 1;
        if (target.hasClass('active')) {
            vote_count -= fact * 1;
            target.removeClass('active');
        } else {
            vote_count += fact * 1;
            if (other.hasClass('active'))
                vote_count += fact * 1;
            target.addClass('active');
            if (thumb_for === 'r')
                other.removeClass('active');
        }
        return vote_count;
    }

    function hide_vote(parent, other, vote_as, count_obj, count) {
        parent.removeClass('active');
        other.removeClass('active');
        if (vote_as == true)
            parent.addClass('active');
        if (vote_as == false)
            other.addClass('active');
        count_obj.html(count);
        return false;
    }

    function submit_thumb(event) {
        var $target = $(event.target);
        var $parent = $target.parent();
        var $vote = $parent.find('.vote-count');
        var thumb_for = $target.data('thumb-for');
        var thumb_as = $target.data('thumb-as');
        var object_pk = $target.data('object-id');

        var vote_count = parseInt($vote.html().trim(), 10);

        if (thumb_as === 'up')
            var $other = $parent.find('.down-arrow');
        else if (thumb_as === 'down')
            var $other = $parent.find('.up-arrow');

        // original vals
        var prev_count = vote_count;
        var prev_thumb;
        if ($target.hasClass('active'))
            prev_thumb = true;
        if ($other.hasClass('active'))
            prev_thumb = false;

        vote_count = show_vote(thumb_as, thumb_for, $target, $other, vote_count);
        $vote.html(vote_count);
        $.ajax({
            type: 'post',
            url: '/thumbs/post/',
            data: {
                'thumb_for': thumb_for,
                'thumb_as': thumb_as,
                'object_pk': object_pk
            },
            success: function(response) {
                if (!response.success) {
                    hide_vote($target, $other, prev_thumb, $vote, prev_count);
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                hide_vote($target, $other, prev_thumb, $vote, prev_count);
            }

        });
    }

    $('body').on('click', "[data-submit='thumb']", function(event) {
        event.stopPropagation();
        $.when(submit_thumb(event)).done();
    });

    $('body').on('click', "[data-submit='auth']", function(event) {
        event.stopPropagation();
        var $target = $(event.target);
        var $parent = $target.parent();

        $SPC_POPOVER.popover('destroy');
        $parent.find("[data-resp='error-info']").popover('show');

    });

});
})(window.jQuery);
