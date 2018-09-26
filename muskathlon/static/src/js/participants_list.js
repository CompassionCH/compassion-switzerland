odoo.define('muskathlon.participants_list', function (require) {
    'use strict';

    var animation = require('web_editor.snippets.animation');
    var Model = require('web.Model');
    var crmEventCompassion = new Model('crm.event.compassion');

    animation.registry.participants_list = animation.Class.extend({
        selector: '.o_participants_list',

        /**
         * Called when widget is started
         */
        start: function () {
            var self = this;
            var tableContent = $(self.$target).find(
                '#participants_list_content');

            // Prevent user's editing
            tableContent.attr('contenteditable', 'False');

            // Get current event id
            var url = window.location.href;
            var eventId = parseInt(
                url.match('/event/[A-z0-9-]+-([0-9]+)/')[1], 10);

            // Call posts
            crmEventCompassion.call('get_muskathlon_participants', [eventId])
                .then(function (participants) {
                    var participantListHtml = '';

                    if (participants.length > 0) {
                        participantListHtml = '<tr><td colspan="3">' +
                        'No participants found...</td></tr>';
                    }

                    participants.forEach(function (participant) {
                        participantListHtml += '<tr>';
                        participantListHtml += '<td><a href="/event/' +
                            eventId + '/participant/' + participant.id + '/">' +
                        participant.name + '</a></td>';
                        participantListHtml += '<td>' + participant.gender +
                        '</td>';
                        participantListHtml += '<td>' + participant.country +
                        '</td>';
                        participantListHtml += '</tr>';
                    });

                    tableContent.html(participantListHtml);
                }).fail(function (err) {
                    console.log('error', err); // eslint-disable-line no-console
                });
        },
    });
});
