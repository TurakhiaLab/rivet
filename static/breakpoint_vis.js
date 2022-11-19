window.onload = draw_breakpoint_viz;

function draw_breakpoint_viz() {
	// Set graph dimensions
	var margin = {top: 30, right: 20, bottom: 30, left: 50},
	    width = 600 - margin.left - margin.right,
	    height = 270 - margin.top - margin.bottom;

	d3.json('/get_breakpoint_data', function(data) {
		var width = 1500, height = 1000;
		var breakpoint_svg =
		    d3.select('#breakpoint_viz')
			.append('svg')
			.attr('width', width + margin.left + margin.right)
			.attr('height', height + margin.top + margin.bottom)
			.append('g')
			.attr(
			    'transform',
			    'translate(' + margin.left + ',' + margin.top +
				')');

		var x =
		    d3.scaleLinear().domain([0, 30000]).range([0, width / 1.5]);

		var y = d3.scaleLinear().domain([0, 20]).range([height / 2, 0]);

		var x_axis = d3.axisBottom().scale(x);

		var y_axis = d3.axisLeft().scale(y);

		// Add the scatterplot
		breakpoint_svg.selectAll('dot')
		    .data(data)
		    .enter()
		    .append('circle')
		    .attr('r', 1)
		    .attr(
			'cx',
			function(data) {
				return x(data['position']);
			})
		    .attr('cy', function(data) {
			    return y(data['count']);
		    });

		// TODO: Now need to draw the lines extending horizontally in
		// each direction

		var x_axis_height = height / 2;

		// Add the X-axis
		breakpoint_svg.append('g')
		    .attr('class', 'x axis')
		    .attr('transform', 'translate(0,' + x_axis_height + ')')
		    .call(x_axis);

		// Add the Y-axis
		breakpoint_svg.append('g').attr('class', 'y axis').call(y_axis);

	});
}
