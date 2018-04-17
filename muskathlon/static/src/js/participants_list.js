// https://github.com/open-synergy/odoo-design-theme/blob/8.0/snippet_latest_posts/views/s_latest_posts.xml

odoo.define('muskathlon.participants_list', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var animation = require('web_editor.snippets.animation');
    var Model = require('web.Model');
    var crmEventCompassion = new Model('crm.event.compassion');

    animation.registry.participants_list = animation.Class.extend({
        selector: ".o_participants_list",
        start: function () {
            var self = this;
            var tableContent = $(self.$target).find('#participants_list_content');

            // prevent user's editing
            tableContent.attr("contenteditable", "False");

            // get current event id
            var url = window.location.href;
            var eventId = parseInt(url.match(/event\/[a-z0-9\-]{1,}-([0-9]{1,})\//)[1]);

            // call posts
            crmEventCompassion.call('getEventParticipants', [eventId]).then(function (participants) {

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
        }
    });
});