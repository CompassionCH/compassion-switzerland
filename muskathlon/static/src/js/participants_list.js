// https://github.com/open-synergy/odoo-design-theme/blob/8.0/snippet_latest_posts/views/s_latest_posts.xml

// console.log('Loaded..');

odoo.define('muskathlon.participants_list', function (require) {
    'use strict';

    // display debug message if set to true
    const DEBUG = true;

    if (DEBUG) console.log('Begin...');

    var ajax = require('web.ajax');
    var animation = require('web_editor.snippets.animation');
    var Model = require('web.Model');
    var crmEventCompassion = new Model('crm.event.compassion');

    animation.registry.participants_list = animation.Class.extend({
        selector: ".o_participants_list",
        start: function () {
            if (DEBUG) console.log('start event fired..');

            var self = this;
            var tableContent = $(self.$target).find('#participants_list_content');

            // prevent user's editing
            tableContent.attr("contenteditable", "False");

            // get current event id
            var url = window.location.href;
            var eventId = parseInt(url.match(/event\/[a-z0-9\-]{1,}-([0-9]{1,})\//)[1]);
            if (DEBUG) console.log(window.location.href, eventId);

            // call posts
            crmEventCompassion.call('getEventParticipants', [eventId]).then(function (participants) {
                if (DEBUG) console.log(participants);

                if (participants.length > 0) {
                    participantListHtml = '<tr><td colspan="3">No participants found...</td></tr>';
                }

                var participantListHtml = '';
                participants.forEach(function (participant) {
                    participantListHtml += '<tr>';
                    participantListHtml += '<td><a href="/event/' + eventId + '/participant/' + participant.id + '/">' + participant.name + '</a></td>';
                    participantListHtml += '<td>' + participant.gender + '</td>';
                    participantListHtml += '<td>' + participant.country + '</td>';
                    participantListHtml += '</tr>';
                });

                tableContent.html(participantListHtml);
            }).fail(function (err) {
                console.log('error', err);
            });

            /* ajax.jsonRpc('/event-participants/707', 'call', {}).then(function (posts) {
                if (DEBUG) console.log(posts);
            }).fail(function (err) {
                if (DEBUG) console.log('err', err);
                return;
            }); */
        }
    });

     if (DEBUG) console.log('End...');

    // var website = odoo.website;
    // website.odoo_website = {};
/*
    var website = require('web.Website');

    website.snippet.participants_list = website.snippet.extend({
        selector: ".js_get_posts",
        start: function () {
            this.redrow();
        },
        stop: function () {
            this.clean();
        },
        redrow: function (debug) {
            this.clean(debug);
            this.build(debug);
        },
        clean: function (debug) {
            this.$target.empty();
        },
        build: function (debug) {
            var self = this,
                limit = self.$target.data("posts_limit"),
                blog_id = self.$target.data("filter_by_blog_id"),
                template = self.$target.data("template"),
                loading = self.$target.data("loading");

            // prevent user's editing
            self.$target.attr("contenteditable", "False");

            // if no data, then use defaults values
            if (!limit) limit = 3;
            if (!template) template = 'snippet_latest_posts.media_list_template';

            // create the domain
            var domain = [['website_published', '=', true]]
            if (blog_id) {
                domain.push(['blog_id', '=', parseInt(blog_id)]);
            }

            // call posts
            openerp.jsonRpc('/event-participants', 'call', {
                'template': template,
                'domain': domain,
                'limit': limit,
            }).then(function (posts) {
                if (loading && loading == true) {
                    // perfrorm an intro animation
                    self.loading(posts, debug);
                } else {
                    // just print the posts
                    $(posts).appendTo(self.$target);
                }
            })
                .fail(function (e) {
                    // debug in js console
                    return;
                });
        },
        loading: function (posts, debug) {
            var self = this,
                $posts = $(posts);

            if (!$posts.first().find(".loading_container") && !$posts.first().is(".loading_container")) {
                console.log("loading_container dont exist??")
                if (debug) {
                    console.info("No '.loading_container' defined \n Please, add a 'loading_container' class to the element that must be filled by the loading bar");
                }
            } else if (!$posts.first().is(".thumb") && !$posts.first().find(".thumb")) {
                console.log("thumb dont exist??")
                if (debug) {
                    console.info("No '.thumb' defined \n Please, add a 'thumb' class to your thumbnail div");
                }
            }
            else {
                $posts.each(function () {
                    var $post = $(this),
                        $load_c = $post.find(".loading_container"),
                        $thumb = $post.find(".thumb"),
                        $progress = $('<div class="progress js-loading"><div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width:0;" /></div>')

                    // prevent precessing empty post
                    if ($post.html() == undefined) {
                        return;
                    }

                    // if can't find loading container or thumb inside the post, then they are the post itself
                    if ($load_c.length == 0) {
                        $load_c = $post
                    }
                    if ($thumb.length == 0) {
                        $thumb = $post
                    }

                    $post.addClass("js-loading");
                    $progress.appendTo($load_c);
                    $post.appendTo(self.$target);

                    var bg = $thumb.css('background-image').replace('url(', '').replace(')', ''),
                        loaded = false;

                    $progress.find(".progress-bar").css("width", "50%").attr("aria-valuenow", "50");

                    var dummyImg = $('<img/>').attr('src', bg)
                        .load(function () {
                            // The post's background image is loaded, let's perform a gracefull intro animation
                            $progress.find(".progress-bar").find(".progress-bar").css("width", "100%").attr("aria-valuenow", "100");
                            setTimeout(function () {
                                self.showPost($post, $progress);
                            }, 500);
                            $(this).remove();
                            loaded = true;
                        });

                    // Show the post after 5sec without wait for thumb loading
                    setTimeout(function () {
                        if (loaded == false) {
                            dummyImg.remove();
                            self.showPost($post, $progress)
                        }
                    }, 5000);

                })
            }
        },
        showPost: function ($post, $progress) {
            $post.removeClass("js-loading");
            $progress.fadeOut(500);
        }
    })
    */
});