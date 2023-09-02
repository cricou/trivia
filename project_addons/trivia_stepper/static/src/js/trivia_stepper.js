odoo.define('trivia_stepper.trivia_here_map_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var field_registry = require('web.field_registry');

    var TriviaHereMapWidget = AbstractField.extend({
        template: 'TriviaHereMapTemplate',
        init: function () {
            this._super.apply(this, arguments);
            this.map = null;
        },

        _render: function () {
            this.$el.empty();
            this.$el.append('<div class="trivia-here-map" style="width: 100%; height: 400px;"><span>test</span></div>');
            // this.initMap();
        },
        
        initMap: function () {
            // Initialize HERE Map
            this.map = new H.Map(
                this.$('.trivia-here-map')[0],
                this.mapConfig()
            );

            // Add default behavior
            var behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(this.map));

            // Create a marker
            var marker = new H.map.Marker({ lat: 52.5, lng: 13.4 });
            this.map.addObject(marker);
        },

        mapConfig: function () {
            var platform = new H.service.Platform({
                apikey: 'YOUR_API_KEY'
            });

            var defaultLayers = platform.createDefaultLayers();
            return {
                center: { lat: 52.5, lng: 13.4 },
                zoom: 10,
                layers: [
                    defaultLayers.vector.normal.map,
                    defaultLayers.vector.normal.traffic
                ]
            };
        },
    });

    field_registry.add('trivia_here_map', TriviaHereMapWidget);
});