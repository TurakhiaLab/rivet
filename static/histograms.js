/**
 * Draw histogram for number of recombinants detected monthly
 * vs number of new infections or number sequenced genomes
 */
window.onload = draw_histogram;

// Button selections for analysis page plot graphs
const full_tree_select = document.getElementById('full_tree_analysis');
const public_tree_select = document.getElementById('public_tree_analysis');
const plot1 = document.getElementById('plot1');
const plot2 = document.getElementById('plot2');
const plot3 = document.getElementById('plot3');


full_tree_select.addEventListener('click', (e) => {
	e.stopPropagation();
	e.preventDefault();

	select_analysis_plot('full', analysis_plot_selected());
	let plot = analysis_plot_selected();
	if (plot === 'plot3') {
		draw_relative_histogram('plot3', 'full');
	} else {
		draw_histogram(plot, 'full');
	}
});

public_tree_select.addEventListener('click', (e) => {
	e.stopPropagation();
	e.preventDefault();
	let plot = analysis_plot_selected();
	select_analysis_plot('public', plot);

	if (plot === 'plot3') {
		draw_relative_histogram('plot3', 'public');
	} else {
		draw_histogram(plot, 'public');
	}
});

plot1.addEventListener('click', (e) => {
	e.stopPropagation();
	e.preventDefault();

	select_analysis_plot(tree_selected(), 'plot1');
	draw_histogram('plot1', tree_selected());
});

plot2.addEventListener('click', (e) => {
	e.stopPropagation();
	e.preventDefault();

	select_analysis_plot(tree_selected(), 'plot2');
	draw_histogram('plot2', tree_selected());
});

plot3.addEventListener('click', (e) => {
	e.stopPropagation();
	e.preventDefault();

	select_analysis_plot(tree_selected(), 'plot3');
	draw_relative_histogram('plot3', tree_selected());
});


function draw_histogram(plot, tree) {
	var right_yAxis_name = 'New Cases';

	if (plot === 'plot1') {
		$('#plot2').removeClass('active');
		$('#plot3').removeClass('active');
		$('#plot1').addClass('active');
	} else if (plot === 'plot2') {
		$('#plot1').removeClass('active');
		$('#plot3').removeClass('active');
		$('#plot2').addClass('active');
		right_yAxis_name = 'New Sequences';
	} else {
		plot = 'plot1';
	}
	// On page load, init with public tree data
	if (!tree) {
		tree = 'public';
	}

	fetch('/get_count_data', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'id': plot, 'tree_type': tree})
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
			if (plot == 'plot1') {
				var corr = ss.sampleCorrelation(
						 data['recomb_counts'],
						 data['month_data'])
					       .toFixed(2);
				console.log(
				    'correlation coefficient plot 1: ', corr);
			}
			if (plot == 'plot2') {
				var corr = ss.sampleCorrelation(
						 data['recomb_counts'],
						 data['month_data'])
					       .toFixed(2);
				console.log(
				    'correlation coefficient plot 2: ', corr);
			}
			var margin =
				{top: 100, right: 200, bottom: 60, left: 80},
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

function draw_relative_histogram(plot, tree) {
	var right_yAxis_name = 'New Cases';

	fetch('/get_relative_data', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'id': plot, 'tree_type': tree})
	}).then(res => {
		res.json().then(data => {
			var div = document.getElementById('cases_histogram');
			if (div) {
				// Clear previous track visualization
				// elements
				d3.selectAll('svg').remove();
			}
			var months = [];
			for (var i = 0; i < data['months'].length; ++i) {
				months[i] = data['months'][i];
			}
			plot_data = [];
			for (var i = 0; i < months.length; ++i) {
				plot_data[i] = {
					'month': months[i],
					'value':
					    Math.round(
						data['axis_data'][i] * 10000) /
					    10000
				};
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

			// Left side y-axis for number of recombinant
			// events
			var yLeft =
			    d3.scaleLinear()
				.domain([0.0, d3.max(data['axis_data'])])
				.range([height, 0]);

			const xAxis = d3.axisBottom(x0);
			const yLeftAxis = d3.axisLeft(yLeft).ticks(20);
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
			    .text('Proportion of new recombination events');

			const tooltip =
			    d3.select('#cases_histogram')
				.append('div')
				.style('position', 'absolute')
				.style('visibility', 'hidden')
				.style('padding', '15px')
				.style('background', 'rgba(0,0,0,0.6)')
				.style('border-radius', '5px')
				.style('color', 'white');

			svg.selectAll('rect')
			    .data(data['axis_data'])
			    .enter()
			    .append('rect')
			    .attr('width', x0.bandwidth())
			    .attr(
				'x',
				function(d, i) {
					return x0(months[i]);
				})
			    .attr(
				'y',
				function(d) {
					return yLeft(d)
				})
			    .attr(
				'height',
				function(d, i) {
					return height - yLeft(d);
				})
			    .style(
				'fill',
				function(d) {
					return '#89ABE3FF';
				})
			    .on('mouseover',
				function(d) {
					var value = d.toLocaleString();
					var name = 'test';
					tooltip.html(`${name}: ${value}`)
					    .style('visibility', 'visible');
					d3.select(this)
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
					.style('fill', '#89ABE3FF');
			    });
		});
	});
}
