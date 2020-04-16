{% include "pybel_vis.js" %}

require.config({
    paths: {
        d3: '//cdnjs.cloudflare.com/ajax/libs/d3/4.5.0/d3.min'
    }
});

var elementInnerHTML = "<div id='{{ chart }}'></div>";

element.append(elementInnerHTML);

require(['d3'], function (d3) {
    return init_d3_force(d3, {{ graph|safe }}, "#{{ chart }}", {{ width }}, {{ height }}, {{ color_map|safe }});
});
