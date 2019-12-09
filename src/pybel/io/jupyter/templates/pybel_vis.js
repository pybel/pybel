function init_d3_force(d3, graph, chart, width, height, function_colors) {
    var focus_node = null;
    var highlight_node = null;

    // Highlight color variables

    // Highlight color of the node boundering
    const highlight_node_boundering = "#4EB2D4";

    // Highlight color of the edge
    const highlighted_link_color = "#4EB2D4";

    // Text highlight color
    const highlight_text = "#4EB2D4";

    // Size when zooming scale
    var size = d3.scalePow().exponent(1)
        .domain([1, 100])
        .range([8, 24]);

    // Simulation parameters
    const linkDistance = 100;
    const fCharge = -1000;
    const linkStrength = 0.7;
    const collideStrength = 1;

    // Simulation defined with variables
    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink()
            .distance(linkDistance)
            .strength(linkStrength)
        )
        .force("collide", d3.forceCollide()
            .radius(function (d) {
                return d.r + 10
            })
            .strength(collideStrength)
        )
        .force("charge", d3.forceManyBody()
            .strength(fCharge)
        )
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("y", d3.forceY(0))
        .force("x", d3.forceX(0));

    // Pin down functionality
    var node_drag = d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
    }

    function releasenode(d) {
        d.fx = null;
        d.fy = null;
    }

    //END Pin down functionality


    /**
     * Gets the best name for a node object
     * @param {object} d object
     * @returns {str} canonical name of the node
     */
    function getCanonicalName(d) {
        if (d.name && !(d.variants || d.reactants || d.products || d.members)) {
            return d.name
        } else if (d.bel) {
            return d.bel
        } else {
            console.log('Undefined node: ' + d);
            return 'UNDEFINED'
        }
    }

    const color_circunferencia = "black";
    const default_link_color = "#AAAAAA";
    const nominal_base_node_size = 8;

    // Normal and highlighted stroke of the links (double the width of the link when highlighted)
    const nominal_stroke = 1.5;

    // Zoom variables
    const min_zoom = 0.1;
    const max_zoom = 10;

    var svg = d3.select(chart).append("svg")
        .attr("width", width)
        .attr("height", height);

    // // Create definition for arrowhead.
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("markerUnits", "strokeWidth")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5");

    // // Create definition for stub.
    svg.append("defs").append("marker")
        .attr("id", "stub")
        .attr("viewBox", "-1 -5 2 10")
        .attr("refX", 15)
        .attr("refY", 0)
        .attr("markerUnits", "strokeWidth")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M 0,0 m -1,-5 L 1,-5 L 1,5 L -1,5 Z");

    // Background
    svg.append("rect")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("fill", "#ffffff")
        .style("pointer-events", "all")
        // Zoom + panning functionality
        .call(d3.zoom()
            .scaleExtent([min_zoom, max_zoom])
            .on("zoom", zoomed))
        .on("dblclick.zoom", null);


    function zoomed() {
        g.attr("transform", d3.event.transform);
    }

    // g = svg object where the graph will be appended
    var g = svg.append("g");

    var linkedByIndex = {};
    graph.links.forEach(function (d) {
        linkedByIndex[d.source + "," + d.target] = true;
    });

    function isConnected(a, b) {
        return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index] || a.index == b.index;
    }

    function ticked() {
        link.attr("x1", function (d) {
            return d.source.x;
        })
            .attr("y1", function (d) {
                return d.source.y;
            })
            .attr("x2", function (d) {
                return d.target.x;
            })
            .attr("y2", function (d) {
                return d.target.y;
            });

        node
            .attr("transform", function (d) {
                return "translate(" + d.x + ", " + d.y + ")";
            });
    }


    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    // Definition of links nodes text...

    var link = g.selectAll(".link")
        .data(graph.links)
        .enter().append("line")
        .style("stroke-width", nominal_stroke)
        .style("stroke", default_link_color)
        .style("stroke-dasharray", function (d) {
            if (['decreases', 'directlyDecreases', 'increases', 'directlyIncreases', 'negativeCorrelation',
                'positiveCorrelation'].indexOf(d.relation) >= 0) {
                return "none"
            } else {
                return "4, 4"
            }
        })
        .attr("marker-start", function (d) {
            if ('positiveCorrelation' == d.relation) {
                return "url(#arrowhead)"
            }
            else if ('negativeCorrelation' == d.relation) {
                return "url(#stub)"
            }
            else {
                return ""
            }
        })
        .attr("marker-end", function (d) {
            if (['increases', 'directlyIncreases', 'positiveCorrelation', 'isA', 'partOf'].indexOf(d.relation) >= 0) {
                return "url(#arrowhead)"
            } else if (['decreases', 'directlyDecreases', 'negativeCorrelation'].indexOf(d.relation) >= 0) {
                return "url(#stub)"
            } else {
                return ""
            }
        });

    var node = g.selectAll(".nodes")
        .data(graph.nodes)
        .enter().append("g")
        .attr("class", "node")
        // Next two lines -> Pin down functionality
        .on('dblclick', releasenode)
        .call(node_drag);

    var circle = node.append("path")
        .attr("d", d3.symbol()
            .size(function (d) {
                return Math.PI * Math.pow(size(d.size) || nominal_base_node_size, 2);
            })
        )
        .attr("class", function (d) {
            return d.function
        })
        .style('fill', function (d) {
            return function_colors[d.function]
        })
        .style("stroke-width", nominal_stroke)
        .style("stroke", color_circunferencia);

    var text = node.append("text")
        .attr("class", "node-name")
        // .attr("id", nodehashes[d])
        .attr("fill", "black")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(function (d) {
            return getCanonicalName(d)
        });

    // Highlight on mouseenter and back to normal on mouseout
    node.on("mouseenter", function (d) {
        set_highlight(d);
    })
        .on("mousedown", function () {
            d3.event.stopPropagation();
        }).on("mouseout", function () {
        exit_highlight();
    });

    function exit_highlight() {
        highlight_node = null;
        if (focus_node === null) {
            if (highlight_node_boundering != color_circunferencia) {
                circle.style("stroke", color_circunferencia);
                text.style("fill", "black");
                link.style("stroke", default_link_color);
            }
        }
    }

    function set_highlight(d) {
        if (focus_node !== null) d = focus_node;
        highlight_node = d;

        if (highlight_node_boundering != color_circunferencia) {
            circle.style("stroke", function (o) {
                return isConnected(d, o) ? highlight_node_boundering : color_circunferencia;
            });
            text.style("fill", function (o) {
                return isConnected(d, o) ? highlight_text : "black";
            });
            link.style("stroke", function (o) {
                return o.source.index == d.index || o.target.index == d.index ? highlighted_link_color : default_link_color;
            });
        }
    }


    // Freeze the graph when space is pressed
    function freezeGraph() {
        // Space button Triggers STOP
        if (d3.event.keyCode == 32) {
            simulation.stop();
        }
    }

    // Call freezeGraph when a key is pressed, freezeGraph checks whether this key is "Space" that triggers the freeze
    d3.select(window).on("keydown", freezeGraph);
}
