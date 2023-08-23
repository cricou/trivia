/* eslint-disable */
odoo.define("trivia_map.HereMapRenderer", function (require) {
    "use strict";

    const BasicRenderer = require("web.BasicRenderer");

    const HereMapRenderer = BasicRenderer.extend({
        className: "o_here_map_view",
        template: "HereMapView.MapView",

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.tours = this.state.data;

        },
        start: function () {
            this._initMap();
            return this._super();
        },
        _getRandomColor: function() {
            const letters = '0123456789ABCDEF';
            let color = '#';
        
            // Generate a random color using hexadecimal values
            for (let i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
        
            // Check the brightness of the color
            // Convert color to RGB values
            const rgb = [
                parseInt(color.slice(1, 3), 16),
                parseInt(color.slice(3, 5), 16),
                parseInt(color.slice(5, 7), 16)
            ];
        
            // Calculate luminance (brightness)
            const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
        
            // Use white or black text based on luminance
            const textColor = luminance > 0.5 ? '#000000' : '#FFFFFF';
        
            return { backgroundColor: color, textColor: textColor };
        },
        _get_marker_list: function(marker_str){

            const markersStr = marker_str.replace(/'/g, '"'); // Remplacer les guillemets simples par des guillemets doubles
            const markersArray = JSON.parse(markersStr); // Parser en tant que JSON valide

            const coordinatesArray = markersArray.map(coordinateStr => {
                const [lat, lng] = coordinateStr.split(',').map(Number);
                return { lat, lng };
            });
            return coordinatesArray
        },
        _initMap: function () {
            var self = this;
            console.log(this);
            var tours = this.tours
            var platform = new H.service.Platform({
                'apikey': ''
              });
         
            var defaultLayers = platform.createDefaultLayers();
   
            this.$(".o_here_map_view").empty();
            
            var checkExist = setInterval(function() {
                
                if ($('#here_map_view').length) {
                    var mapElement = document.getElementById("here_map_view");
                    console.log(mapElement)
                    var map = new H.Map(
                        mapElement,
                        defaultLayers.vector.normal.map,
                        {
                          zoom: 10,
                          center: { lng: 13.4, lat: 52.51 },
                          pixelRatio: window.devicePixelRatio || 1
                        });
                        window.addEventListener('resize', () => map.getViewPort().resize());
                        var behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(map));
                        var ui = H.ui.UI.createDefault(map, defaultLayers);
                        
                       
                        var group = new H.map.Group();
                        tours.forEach(element => {
                            var colors = self._getRandomColor();
                            console.log(element);
                            var markers_str = element.data.here_checkpoints; 
                            var markers_array = self._get_marker_list(markers_str);
                            console.log(markers_array)
                            var number = 1;
                            
                            
                            markers_array.forEach(element => {
                                var svgMarkup = '<svg width="18" height="18" ' +
                                            'xmlns="http://www.w3.org/2000/svg">' +
                                            '<circle cx="8" cy="8" r="8" ' +
                                            'fill="' + colors.backgroundColor + '" stroke="white" stroke-width="1" />' +
                                            '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" ' +
                                            'fill="' + colors.textColor + '" font-size="10">' + number + '</text>' +
                                            '</svg>',
                                            dotIcon = new H.map.Icon(svgMarkup, {anchor: {x:8, y:8}}),
                                            i,
                                            j;
                                number += 1;
                                var marker = new H.map.Marker({
                                    lat: element.lat,
                                    lng: element.lng},
                                    {icon: dotIcon});
                                group.addObject(marker);
                            });

                            var polyline_str = element.data.here_polylines; // Votre chaîne de caractères
                            polyline_str = polyline_str.replace(/'/g, '"'); // Remplacez les guillemets simples par des guillemets doubles
                            var polyline_array = JSON.parse(polyline_str);
                    
                            polyline_array.forEach(element => {
                                let linestring = H.geo.LineString.fromFlexiblePolyline(element);
                                var routeOutline = new H.map.Polyline(linestring, {
                                    style: {
                                    lineWidth: 5,
                                    strokeColor: colors.backgroundColor,
                                    lineTailCap: 'arrow-tail',
                                    lineHeadCap: 'arrow-head'
                                    }
                                });
                                // Create a patterned polyline:
                                var routeArrows = new H.map.Polyline(linestring, {
                                style: {
                                    lineWidth: 5,
                                    fillColor: 'white',
                                    strokeColor: colors.textColor,
                                    lineDash: [0, 2],
                                    lineTailCap: 'arrow-tail',
                                    lineHeadCap: 'arrow-head' }
                                }
                                );
                                // create a group that represents the route line and contains
                                // outline and the pattern
                                
                                group.addObjects([routeOutline, routeArrows]);
                                
                            });
                            
                        });
                        map.addObjects([group]);
                        map.getViewModel().setLookAtData({bounds: group.getBoundingBox()});
                        
                    clearInterval(checkExist);
                }
             }, 100);
            
            
        },
    });

    return HereMapRenderer;
});