/**
 * Draw histogram for number of recombinants detected monthly
 * vs number of new infections or number sequenced genomes
 */
window.onload = draw_histogram;

function draw_histogram(plot) {
	var right_yAxis_name = 'New Cases';
	if (plot == 'plot1') {
		$('#plot2').removeClass('active');
		$('#plot1').addClass('active');
	} else if (plot == 'plot2') {
		$('#plot1').removeClass('active');
		$('#plot2').addClass('active');
		right_yAxis_name = 'New Sequences';
	} else {
		plot = 'plot1';
	}

	fetch('/get_count_data', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'id': plot})
	}).then(res => {
		res.json().then(data => {
			var div = document.getElementById('cases_histogram');
			if (div) {
				// Clear previous track visualization elements
				d3.selectAll('svg').remove();
			}
			var months = [];
			for (var i = 0; i < data['data'].length; ++i) {
				months[i] = data['data'][i]['month']
			}
			var plot_labels = {
				'New Cases':
				    'Number of new infections reported',
				'New Sequences':
				    'Number of new genome sequences added'
			};
			var margin =
				{top: 100, right: 110, bottom: 60, left: 80},
			    width = 2000 - margin.left - margin.right,
			    height = 900 - margin.top - margin.bottom;

			var colors =
			    d3.scaleOrdinal().range(['#EA738DFF', '#89ABE3FF']);

			var svg =
			    d3.select('#cases_histogram')
				.append('svg')
				.attr(
				    'width', width + margin.left + margin.right)
				.attr(
				    'height',
				    height + margin.top + margin.bottom)
				.append('g')
				.attr(
				    'transform',
				    'translate(' + margin.left + ',' +
					margin.top + ')');

			var x0 = d3.scaleBand()
				     .domain(months)
				     .range([0, width])
				     .paddingInner(0.5);
			var x1 =
			    d3.scaleBand()
				.domain(
				    ['Recombinants Count', right_yAxis_name])
				.rangeRound([0, x0.bandwidth()]);

			// Left side y-axis for number of recombinant
			// events
			var yLeft =
			    d3.scaleLinear()
				.domain([0, d3.max(data['recomb_counts'])])
				.range([height, 0]);

			// Right side y-axis for number of new cases
			var yRight =
			    d3.scaleLinear()
				.domain([0, d3.max(data['month_data'])])
				.range([height, 0]);

			const xAxis = d3.axisBottom(x0);
			const yLeftAxis = d3.axisLeft(yLeft).ticks(20);
			const yRightAxis = d3.axisRight(yRight).ticks(20);

			svg.append('g')
			    .attr('class', 'bottomAxis')
			    .attr('transform', 'translate(0,' + height + ')')
			    .data([months])
			    .call(d3.axisBottom(x0))
			    .selectAll('text')
			    .style('text-anchor', 'end')
			    .attr('dx', '-.8em')
			    .attr('dy', '.15em')
			    .attr('transform', 'rotate(-65)');

			svg.append('g')
			    .attr('class', 'y0 axis')
			    .call(yLeftAxis)
			    .append('text')
			    .attr('transform', 'rotate(-90)')
			    .attr('x', -85)
			    .attr('y', -60)
			    .attr('dominant-baseline', 'central')
			    .style('font-size', '24px')
			    .style('fill', '#89ABE3FF')
			    .text(
				'Number of new recombination events inferred');

			svg.append('g')
			    .attr('class', 'y1 axis')
			    .attr('transform', 'translate(' + width + ',0)')
			    .call(yRightAxis)
			    .append('text')
			    .attr('transform', 'rotate(-90)')
			    .attr('x', -550)
			    .attr('y', 95)
			    .attr('dominant-baseline', 'central')
			    .style('font-size', '24px')
			    .style('fill', '#EA738DFF')
			    .text(plot_labels[right_yAxis_name]);

			const tooltip =
			    d3.select('#cases_histogram')
				.append('div')
				.style('position', 'absolute')
				.style('visibility', 'hidden')
				.style('padding', '15px')
				.style('background', 'rgba(0,0,0,0.6)')
				.style('border-radius', '5px')
				.style('color', 'white');

			var graph = svg.selectAll('.month')
					.data(data['data'])
					.enter()
					.append('g')
					.attr('class', 'g')
					.attr('transform', function(d) {
						return 'translate(' +
						    x0(d.month) + ',0)';
					});

			graph.selectAll('rect')
			    .data(function(d) {
				    return d.values;
			    })
			    .enter()
			    .append('rect')
			    .attr('width', x1.bandwidth())
			    .attr(
				'x',
				function(d) {
					return x1(d.key);
				})
			    .attr(
				'y',
				function(d) {
					if (d.key == 'Recombinants Count') {
						return yLeft(d.value);
					} else if (d.key == right_yAxis_name) {
						return yRight(d.value);
					}
				})
			    .attr(
				'height',
				function(d) {
					if (d.key == 'Recombinants Count') {
						return height - yLeft(d.value);
					} else {
						return height - yRight(d.value);
					}
				})
			    .style(
				'fill',
				function(d) {
					return colors(d.key);
				})
			    .on('mouseover',
				function(d) {
					var value = d['value'].toLocaleString();
					var name = d['key'];
					tooltip.html(`${name}: ${value}`)
					    .style('visibility', 'visible');
					d3.select(this)
					    //.style('fill', 'orange')
					    .style('fill', '#1fd655')
					    .attr('stroke-width', '1')
					    .attr('stroke', 'black');
				})
			    .on('mousemove',
				function() {
					tooltip
					    .style(
						'top',
						(event.pageY - 10) + 'px')
					    .style(
						'left',
						(event.pageX + 10) + 'px');
				})
			    .on('mouseout', function() {
				    tooltip.html(``).style(
					'visibility', 'hidden');
				    d3.select(this)
					.attr('stroke-width', '0')
					.style('fill', function(d) {
						return colors(d.key);
					});
			    });

			const legend_square_size = 25;
			var legend =
			    svg.selectAll('labels')
				.data([
					plot_labels[right_yAxis_name],
					'Number of new recombination events inferred'
				])
				.enter()
				.append('g')
				.attr('transform', function(d, i) {
					return 'translate(0,' + i * 35 + ')';
				});

			legend.append('rect')
			    .attr('x', 50)
			    .attr('y', -100)
			    .attr('width', legend_square_size)
			    .attr('height', legend_square_size)
			    .style('fill', colors);
			legend.append('text')
			    .attr('x', 80)
			    .attr('y', -90)
			    .attr('dy', '.50em')
			    .style('text-anchor', 'start')
			    .text(function(d) {
				    return d;
			    });
		});
	});
}
