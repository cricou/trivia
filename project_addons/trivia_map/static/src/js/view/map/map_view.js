/* eslint-disable */
odoo.define("trivia_map.HereMapView", function (require) {
    "use strict";

    const BasicView = require("web.BasicView");
    const core = require("web.core");
    const HereMapModel = require("trivia_map.HereMapModel");
    const HereMapRenderer = require("trivia_map.HereMapRenderer");
    const HereMapController = require("trivia_map.HereMapController");


    const HereMapView = BasicView.extend({
        accesskey: "m",
        display_name: "Here Map",
        icon: "fa-map-o",
        config: _.extend({}, BasicView.prototype.config, {
            Model: HereMapModel,
            Renderer: HereMapRenderer,
            Controller: HereMapController,
        }),
        viewType: "here_map",
        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
        },

    });

    return HereMapView;
});