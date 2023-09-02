odoo.define("trivia_map.view_registry", function (require) {
    "use strict";

    var MapView = require("trivia_map.HereMapView");
    var view_registry = require("web.view_registry");

    view_registry.add("here_map", MapView);
});