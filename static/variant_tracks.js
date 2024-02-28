// Track constants
const track_width = 1750;
const track_x_position = 300;
const border_height = 700;
const border_width = 1900;
const outer_buffer = 50;  // Enought to be larger than height of track
const buffer_btw_tracks = 5;
const buffer_btw_bases = 5;
const polygon_buffer = 150;
const coordinate_track_height = 50;
const coordinate_outer_buffer = 150;
const coordinate_outermost_buffer = 30;

function add_small_trio_track(track_svg, y_position, square_dims, d) {
  // New y position to update and return for next track added above
  var new_y = y_position;

  var color = '#c6c6c6';

  var donor_snps = [];
  var recomb_snps = [];
  var acceptor_snps = [];
  var reference_snps = [];

  for (const [key, value] of Object.entries(d['SNPS'])) {
    donor_snps.push(value['Donor']);
    recomb_snps.push(value['Recomb']);
    acceptor_snps.push(value['Acceptor']);
    reference_snps.push(value['Reference']);
  }

  var small_track_width = (reference_snps.length * square_dims) +
      ((reference_snps.length - 1) * buffer_btw_bases);

  // Add donor track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', small_track_width)
      .attr('height', square_dims)
      .attr('fill', color);

  // Add snps to donor track
  add_bases_to_track(
      track_svg, donor_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);

  // Add label to donor track
  var donor_label_text = 'Donor';
  var label_node_id = d['NODE_IDS']['Donor'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, donor_label_text,
      label_node_id, d);

  // Reposition y
  new_y -= (square_dims + buffer_btw_tracks);

  // Add recombinant track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', small_track_width)
      .attr('height', square_dims)
      .attr('fill', color);

  // Add snps to recomb track
  add_bases_to_track(
      track_svg, recomb_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);

  var recomb_label_text = 'Recombinant';
  var label_node_id = d['NODE_IDS']['Recomb'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, recomb_label_text,
      label_node_id, d);

  new_y -= (square_dims + buffer_btw_tracks);

  // Add acceptor track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', small_track_width)
      .attr('height', square_dims)
      .attr('fill', color);

  // Add snps to acceptor track
  add_bases_to_track(
      track_svg, acceptor_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);

  var acceptor_label_text = 'Acceptor';
  var label_node_id = d['NODE_IDS']['Acceptor'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, acceptor_label_text,
      label_node_id, d);

  var snp_positions = [];
  for (const [key, value] of Object.entries(d['SNPS'])) {
    snp_positions.push(key);
  }

  // Set domain for top position tick mark axis
  var x = d3.scaleBand().domain(snp_positions).range([
    track_x_position, small_track_width + track_x_position
  ]);

  track_svg.append('g')
      .attr('class', 'TopAxis')
      .data([snp_positions])
      .attr(
	  'transform',
	  //'translate(0,570)')
	  // Vertical position
	  `translate(0,${new_y - buffer_btw_tracks - 5})`)
      .call(d3.axisTop(x))
      .selectAll('text')
      .style('text-anchor', 'start')
      .attr('dx', '1em')
      .attr('dy', '.2em')
      .style('font-size', '15px')
      .attr('transform', 'rotate(-65)')
      // TODO: Add mouseover highlighting
      .on('mouseover', function(d) {
	d3.select(this).attr('fill', '#ff0000');
      });

  // Update y position to inform next track
  new_y -= (square_dims + buffer_btw_tracks);

  return [track_svg, new_y];
}


function add_small_reference_track(
    track_svg, polygon_buffer, y_position, square_dims, reference_snps,
    snp_positions, d) {
  // New y position to update
  var new_y = y_position;

  var small_track_width = (reference_snps.length * square_dims) +
      ((reference_snps.length - 1) * buffer_btw_bases);

  // Grey color for reference track
  var color = d['COLOR']['reference_track'];

  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - polygon_buffer - buffer_btw_tracks)
      .attr('width', small_track_width)
      // Autoscale track height based on even paritioning
      // of square dimensions
      .attr('height', square_dims)
      .attr('fill', color);
  track_svg.append('text')
      .attr('x', 0)
      .attr('y', track_x_position + square_dims)
      .style('font-size', '20px');

  var y_pos = new_y - polygon_buffer - buffer_btw_tracks;

  add_bases_to_track(
      track_svg, reference_snps, track_x_position, y_pos, square_dims, true, d);

  // Draw polygons connecting genomic coordinates with snp
  // columns
  var top_line = 0;
  var left_square = 0;
  var right_square = 0;

  // Add label to left side of reference track
  var ref_label_text = 'Reference';
  var label_node_id = 'None';
  add_track_label(
      track_svg, new_y - polygon_buffer - buffer_btw_tracks, square_dims,
      ref_label_text, label_node_id, d);

  return [track_svg, new_y - buffer_btw_tracks - polygon_buffer - square_dims];
}


function add_small_coordinate_track(track_svg, y_position, data, square_dims) {
  // New y position to update and return as new track is
  // added above previous one
  var new_y = y_position;

  // Get all genomic positions
  var snp_positions = [];

  for (const [key, value] of Object.entries(data['SNPS'])) {
    snp_positions.push(parseInt(key));
  }
  // Small track half the size of regular track
  var small_track_width = track_width / 1.5;

  //  Add reference at bottom of border
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', border_height - coordinate_outer_buffer)
      .attr('width', small_track_width)
      .attr('height', coordinate_track_height)
      //.attr('fill', '#b2b2b2');
      .attr('fill', '#dadada');

  var zero = 0;
  var x_axis_height =
      border_height - coordinate_outer_buffer + coordinate_track_height;
  var x_axis_pos = [zero.toString(), x_axis_height.toString()].join(',');

  var x = d3.scaleLinear().domain([0, data['GENOME_SIZE']]).range([
    track_x_position, small_track_width + track_x_position
  ]);

  track_svg.append('g')
      .attr(
	  'transform',
	  // TODO: Parameterize this translation
	  'translate(0,600)')
      .call(d3.axisBottom(x).tickValues(data['GENOMIC_RANGE']));

  //  Create x-axis label for coordinate track
  track_svg.append('text')
      .attr('class', 'x label')
      .attr('text-anchor', 'end')
      //.attr('x', small_track_width / 1.5 + track_x_position)
      .attr('x', 280)
      .attr('y', border_height - 60)
      .attr('font-weight', 700)
      .style('font-size', '20px')
      .text('Genomic Coordinate');

  var breakpoint_data = data['BREAKPOINTS'];

  track_svg.append('rect')
      .data([breakpoint_data])
      .attr(
	  'width',
	  function(d) {
	    try {
	      return (x(d['breakpoint1'].end) - x(d['breakpoint1'].xpos))
	    } catch (error) {
	      return 0;
	    }
	  })
      .attr('height', coordinate_track_height)
      .attr(
	  'x',
	  function(d) {
	    try {
	      return x(d['breakpoint1'].xpos)
	    } catch (error) {
	      return 0;
	    }
	  })
      .attr('y', border_height - coordinate_outer_buffer)
      //.attr('fill', '#b2b2b2')
      .attr('fill', '#dadada')

      //.transition()
      // Delay of the transition
      //.delay(1000)
      //.duration(3000)
      .attr('fill', data['COLOR']['breakpoint_intervals']);

  track_svg.append('rect')
      .data([breakpoint_data])
      .attr(
	  'width',
	  function(d) {
	    try {
	      return (x(d['breakpoint2'].end) - x(d['breakpoint2'].xpos))
	    } catch (error) {
	      return 0
	    }
	  })
      .attr('height', coordinate_track_height)
      .attr(
	  'x',
	  function(d) {
	    try {
	      return x(d['breakpoint2'].xpos)
	    } catch (error) {
	      return 0;
	    }
	  })
      .attr('y', border_height - coordinate_outer_buffer)
      //.attr('fill', '#b2b2b2')
      .attr('fill', '#dadada')

      //.transition()
      //.delay(1000)
      //.duration(3000)
      .attr('fill', data['COLOR']['breakpoint_intervals']);

  // Drawing polygons
  const dot = track_svg.append('g')
		  .selectAll('dot')
		  .data(snp_positions)
		  .enter()
		  .append('circle')
		  .attr('cx', (d) => x(d))
		  .attr('cy', border_height - coordinate_outer_buffer)
		  .attr('r', 0.1)
		  .style('fill', 'darkblue')

  var lines =
      track_svg.selectAll('lines')
	  .data(snp_positions)
	  .enter()
	  .append('line')
	  .attr('class', 'lines')
	  .attr('x1', (d) => x(d))
	  .attr('x2', (d) => x(d))
	  .attr('y1', border_height - coordinate_outer_buffer)
	  .attr(
	      'y2',
	      border_height - coordinate_outer_buffer + coordinate_track_height)
	  .attr('stroke-width', '1.0')
	  //.attr('stroke', '#b2b2b2')
	  .attr('stroke', '#dadada')

	  //.transition()
	  // Added a delay so the lines would appear in sequential
	  // increasing order
	  //.duration(function(d, i) {
	  // var delay = i * 200;
	  // return delay;
	  //})
	  //.duration(1000)
	  // Fade in line posiiton color
	  // Speed slightly faster than matching polygons.
	  .attr('stroke', '#dd760b');


  // Get informative site positions
  var info_sites = data['INFO_SITES'];

  var num = 0;
  var circle =
      track_svg.selectAll('polygon')
	  .data(snp_positions)
	  .enter()
	  .append('polygon')
	  .attr(
	      'points',
	      function(d, i) {
		var x_offset = x(d);
		let left_y = border_height - coordinate_outer_buffer;
		let left = [x_offset.toString(), left_y.toString()].join(',');

		let top_y = border_height - coordinate_outer_buffer -
		    polygon_buffer + square_dims - buffer_btw_tracks;
		// (square_dims*i) gives offset for
		// num square
		let top_x = track_x_position +
		    ((i * square_dims) + (i * buffer_btw_tracks));
		let _top = [top_x.toString(), top_y.toString()].join(',');

		let right_y = border_height - coordinate_outer_buffer -
		    polygon_buffer + square_dims - buffer_btw_tracks;
		let right_x = track_x_position +
		    (i * square_dims + (i * buffer_btw_tracks)) + square_dims;
		let right = [right_x.toString(), right_y.toString()].join(',');

		// Join all points
		// together in formatted
		// points string
		polygon_points = [left, _top, right].join(' ');


		return polygon_points;
	      })
	  .attr('fill', '#FFFFFF')

	  //.transition()
	  //.duration(function(d, i) {
	  //	var delay = i * 200;
	  // return delay;
	  //})

	  .attr('fill', function(d, i) {
	    var color;
	    if (d.toString() in info_sites) {
	      var match = info_sites[d];
	      color = determine_informative(match, data['COLOR']);
	    } else {
	      // Otherwise not an informative site,
	      // don't highlight
	      color = data['COLOR']['non_informative_site'];
	    }
	    return color;
	  });

  var region_sizes = [232, 13205, 8095];
  var regions = [1, 233, 13436, 21531];

  var color = '#474747';
  var region_names = ['ORF1a', 'ORF1b', 'S', '3a', 'E', 'M', 'N'];
  var region_colors = [
    '#add8e6', '#ffb1b1', '#ffffe0', '#ffdc9d', '#bcf5bc', '#ffceff', '#ffa500',
    '#1e90ff'
  ];
  var region_widths = [13203, 8095, 3767, 858, 230, 800, 1000, 1268];
  var starting_x_coord = [232, 13203, 8095, 3767, 858, 230, 800, 1000, 1268];

  // TODO: Extract this region data from json passed from
  // backend processing of gene annotation files
  var region_data = {
    'ORF1a': {xpos: 274, end: 13409, color: '#333333'},
    'ORF1b': {xpos: 13409, end: 21531, color: '#333333'},
    'S': {xpos: 21531, end: 25268, color: '#333333'},
    '3a': {xpos: 25268, end: 26126, color: '#333333'},
    'E': {xpos: 26126, end: 26471, color: '#333333'},
    'M': {xpos: 26471, end: 28471, color: '#333333'},
    'N': {xpos: 28471, end: 29903, color: '#333333'}
  };

  draw_genomic_region(track_svg, region_names, region_data, x);

  return [track_svg, border_height - coordinate_outer_buffer];
}

function handle_zero_snps(svg) {
  svg.append('text')
      .attr('x', border_width / 2)
      .attr('y', border_height / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', 60)
      .style('font-weight', 'bold')
      .style('fill', 'red')
      .text('No SNVs to display for the selected recombinant.');
}

function hide_aa_labels(track_svg) {
  // Hide amino acid track, restore SNV view title
  d3.select('#plot_title').style('opacity', 1);
  d3.select('#aa_track_title').remove();
  d3.selectAll('#AALabels').remove();
  d3.selectAll('.TopAxisAA').remove();
}


function add_aa_labels(
    track_svg, y_position, snp_positions, square_dims, num_snps, d,
    nt_positions, aa_mutations) {

  // Hide plot title
  d3.select('#plot_title').style('opacity', 0);
  // Add title to left of AA track
  let label_x_offset = 180;
  track_svg.append('text')
      .attr('id', 'aa_track_title')
      .attr('x', label_x_offset + 100)
      .attr('y', 210)
      .attr('text-anchor', 'start')
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'central')
      .attr('font-weight', 400)
      .style('font-size', '15px')
      .text('Coding Amino Acid Mutations');

  var acceptor_snps = [];
  for (const [key, value] of Object.entries(d['SNPS'])) {
    acceptor_snps.push(value['Acceptor']);
  }
  var new_y = y_position;

  var num_snps = acceptor_snps.length;
  var label_width =
      (num_snps * square_dims + (num_snps - 1) * buffer_btw_bases) +
      track_x_position;

  var x = d3.scaleBand().domain(snp_positions).range([
    track_x_position, label_width
  ]);

  // Get informative site positions
  var info_sites = d['INFO_SITES'];
  var colors = d['COLOR'];
  track_svg.append('g')
      .attr('class', 'TopAxisAA')
      .data([snp_positions])
      .attr('transform', `translate(0,${new_y - buffer_btw_tracks - 5})`)
      .call(d3.axisTop(x))
      .selectAll('text')
      .style('text-anchor', 'start')
      .attr('dx', '1em')
      .attr('dy', '.2em')
      .style('font-size', '15px')
      .attr('transform', 'rotate(-65)')
      .attr('id', 'AALabels')
      .style(
	  'fill',
	  function(d, i) {
	    var color;
	    if (d.toString() in info_sites) {
	      var match = info_sites[d];
	      color = determine_informative(match, colors);
	    } else {
	      // Otherwise not an informative site, don't
	      // highlight
	      color = colors['non_informative_site'];
	    }
	    return color;
	  })
      .style('opacity', function(d, i) {

	if (!nt_positions.includes(d.toString())) {
	  return '0';
	} else {
	  let index = nt_positions.indexOf(d.toString());
	  let aa_mut = aa_mutations[index].toString();
	  d3.select(this).text(aa_mut);
	  return '1';
	}
      });
  track_svg.selectAll('.TopAxisAA path').style('stroke', '#FFFFFF');
}

function add_column_label(
    track_svg, label_y_position, x_pos, square_dims, label_text) {
  // Add label above each column
  track_svg.append('rect')
      .attr('x', x_pos)
      .attr('y', label_y_position)
      .attr('width', square_dims)
      .attr('height', square_dims * 2)
      // Background rect white, so only text label shows
      //.attr('fill', '#D3D3D3');
      .attr('fill', '#D3D3D3');

  // Add text position label above each track
  track_svg.append('text')
      .attr('x', x_pos + (square_dims / 2))
      .attr('y', (label_y_position + (square_dims / 2)))
      .text(label_text)
      .style('text-anchor', 'end')
      .attr('fill', '#c45f00')
      .attr('dominant-baseline', 'central')
      .attr('font-weight', 700)
      .style('font-size', '20px')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', function(d) {
	return 'rotate(-90)'
      });
}


function add_column_position_labels(
    track_svg, y_position, snp_positions, square_dims, num_snps, d) {
  // Move y_position past top track
  y_position -= (square_dims + buffer_btw_bases)


  // Starting x_pos on lefthand side of visual
  var x_pos = track_x_position;
  for (pos of snp_positions) {
    add_column_label(track_svg, y_position, x_pos, square_dims, pos.toString());

    // Update x_pos
    x_pos += (square_dims + buffer_btw_bases);
  }
}

function init_coordinate_track(track_svg, y_position, data) {
  // New y position to update and return as new track is
  // added above previous one
  var new_y = y_position;
  const init_track_x_position = 100;

  track_svg
      .append('text')
      //.attr('x', 1000)
      .attr('x', 800)
      .attr('y', 300)
      .attr('text-anchor', 'middle')
      .attr('font-size', 28)
      .style('font-weight', 'bold')
      .text(
	  'Select a table entry below to view  the single-nucleotide variation in the recombinant and its parents');

  // Add initial genomic track
  track_svg.append('rect')
      .attr('x', init_track_x_position)
      //.attr('x', track_x_position)
      .attr('y', border_height - coordinate_outer_buffer)
      .attr('width', track_width)
      .attr('height', coordinate_track_height)
      //.attr('fill', '#b2b2b2');
      .attr('fill', '#dadada');

  var zero = 0;
  var x_axis_height =
      border_height - coordinate_outer_buffer + coordinate_track_height;
  var x_axis_pos = [zero.toString(), x_axis_height.toString()].join(',');
  var x = d3.scaleLinear().domain([0, data['GENOME_SIZE']]).range([
    // track_x_position, track_width + track_x_position
    init_track_x_position, track_width + init_track_x_position
  ]);
  track_svg.append('g')
      .attr('transform', 'translate(0,600)')
      .call(d3.axisBottom(x).tickValues(data['GENOMIC_RANGE']));

  //  Create x-axis label for coordinate track
  /*
track_svg.append('text')
.attr('class', 'x label')
.attr('text-anchor', 'end')
.attr('x', border_width / 1.75)
.attr('y', border_height - 60)
.attr('font-weight', 700)
.style('font-size', '20px')
.text('Genomic Coordinate');
*/

  let region_names = Object.keys(data['REGION_DATA']);
  let region_data = data['REGION_DATA'];

  draw_genomic_region(track_svg, region_names, region_data, x);

  return [track_svg, border_height - coordinate_outer_buffer];
}

function append_interval(test, breakpoint_data, breakpoint, x) {
  test.append('rect')
      .attr(
	  'width',
	  function(d) {
	    return (x(d[breakpoint].end) - x(d[breakpoint].xpos))
	  })
      .attr('height', coordinate_track_height)
      .attr(
	  'x',
	  function(d) {
	    return x(d[breakpoint].xpos)
	  })
      .attr('y', border_height - coordinate_outer_buffer)
      //.attr('fill', '#b2b2b2')
      .attr('fill', '#dadada')
      .transition()
      .duration(10)
      .attr('fill', data['COLOR']['breakpoint_intervals']);
}


function add_breakpoint_internals(track_svg, data) {
  track_svg
      .append('rect')
      // X-position = breakpoint interval start
      .attr('x', track_x_position + 100)
      // Same as coordinate track
      .attr('y', border_height - coordinate_outer_buffer)
      //  width = breakpoint interval end
      .attr('width', 50)
      // Same as coordinate track
      .attr('height', coordinate_track_height)
      //.attr('fill', '#b2b2b2')
      .attr('fill', '#dadada')
      .transition()
      .duration(30)
      .attr('fill', data['COLOR']['breakpoint_intervals']);
}

function add_track_label(
    track_svg, label_y_position, square_dims, label_text, label_node_id, d) {
  let label_halfway = square_dims / 2;
  let label_width = 100;
  // Left side track label buffer distance from each track
  let label_x_offset = 180;

  if (d != null) {
    // Add label to left of reference track
    track_svg.append('rect')
	.attr('x', label_x_offset)
	.attr('y', label_y_position)
	.attr('width', label_width)
	// The track height scales based on even paritioning of
	// square dimensions
	.attr('height', square_dims)
	// Background rect white, so only text label shows
	.attr('fill', '#ffffff');

    // Add text labels to left of each track
    track_svg.append('text')
	.attr('x', label_x_offset + label_width)
	.attr('y', (label_y_position + (square_dims / 2)))
	.text(label_text)
	.attr('id', label_text)
	.attr('text-anchor', 'end')
	.attr('dominant-baseline', 'central')
	.attr('font-weight', 700)
	.style('font-size', '16px')
	.on('click',
	    function(d) {
	      // Fetch and display the descendants for the
	      // selected recombinant node id
	      display_descendants(label_node_id);
	      d3.select('#' + label_text)
	    })
	.on('mouseover',
	    function(d) {
	      d3.select(this).text(label_node_id).transition().delay(10);

	      d3.select(this)
		  .style('fill', '#4169E1')
		  .attr('stroke-width', '1')
		  .style('opacity', 3);
	    })
	.on('mouseleave', function(d) {
	  d3.select(this)
	      .text(label_text)
	      .style('fill', 'black')
	      .style('opacity', 1)
	      .transition()
	      .delay(10)
	});
  }
  if (label_text == 'Acceptor' &&
      document.querySelector('#download_all_descendants').style.visibility !=
	  'hidden') {
    // Add text instuctions above tracks
    track_svg.append('text')
	.attr('x', label_x_offset + label_width)
	.attr('y', (label_y_position + (square_dims / 2)) - 50)
	.text('Click below to view descendants')
	// TODO: Uniquely label text that will not be included in
	// SVG download, only for browser interactivity
	//.attr('id', label_text)
	.attr('id', 'click_desc_label')
	.attr('text-anchor', 'end')
	.attr('dominant-baseline', 'central')
	.attr('font-weight', 400)
	.style('font-size', '8px');
  }
}

// TODO: Remove, not in use
function format_polygon_points(square_dims) {
  let left_y = border_height - coordinate_outer_buffer;
  let left = [track_x_position.toString(), left_y.toString()].join(',');

  let top_y = border_height - coordinate_outer_buffer - polygon_buffer +
      square_dims - buffer_btw_tracks;
  let _top = [track_x_position.toString(), top_y.toString()].join(',');

  let right_y = border_height - coordinate_outer_buffer - polygon_buffer +
      square_dims - buffer_btw_tracks;
  let right_x = track_x_position + square_dims;
  let right = [right_x.toString(), right_y.toString()].join(',');

  // Join all points together in formatted points string
  polygon_points = [left, _top, right].join(' ');

  return polygon_points;
}

function append_g(g, region_data, region, x) {
  const genomic_region_dims = 30;

  g.append('rect')
      // Width mapped to genomic region coordinates
      .attr(
	  'width',
	  function(d) {
	    return (x(d[region].end) - x(d[region].xpos))
	  })
      .attr('height', genomic_region_dims)
      // X-coordinate as a function of genomic region
      // (mapping to 1-30k)
      .attr(
	  'x',
	  function(d) {
	    return x(d[region].xpos)
	  })
      .attr(
	  'y',
	  border_height - coordinate_outermost_buffer - genomic_region_dims)
      .attr('fill', region_data[region].color)
      .on('mouseover',
	  function(d) {
	    d3.select(this)
		.attr('fill', '#4169E1')
		.style('stroke', 'white')
		.attr('stroke-width', '3');
	  })
      .on('mouseleave',
	  function(d) {
	    d3.select(this)
		.attr('fill', region_data[region].color)
		.attr('stroke', 'white')
		.attr('stroke-width', '1')
	  })
      .style('stroke', 'white')
      .attr('stroke-width', '1')

      .on('click', function(d) {
	// TODO: Finish select SNVs falling in specific region
	// feature
	console.log('CLICKED ON REGION: ', region);
      });

  // Add text label to genomic region
  // TODO: Fix mouseover text issue
  g.append('text')
      .attr(
	  'x',
	  function(d) {
	    return (
		x(d[region].xpos) +
		((x(d[region].end) - x(d[region].xpos)) / 2))
	  })
      .attr(
	  'y',
	  border_height - coordinate_outermost_buffer -
	      (genomic_region_dims / 2))
      .text(function(d) {
	let length = d[region].end - d[region].xpos;
	let region_dim = x(d[region].end) - x(d[region].xpos);
	if (region_dim < 30 && region.length != 1) {
	  return;
	}
	return region;
      })

      // Center text char in square
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', 'white')
      .style('font-size', '10px');
}

function draw_genomic_region(track_svg, region_names, region_data, x) {
  // Add genomic region rect
  var g = track_svg.selectAll('.rect')
	      .data([region_data])
	      .enter()
	      .append('g')
	      .classed('rect', true)

  for (region of region_names) {
    append_g(g, region_data, region, x);
  }
}

function draw_polypons(
    track_svg, square_dims, top_line, left_square, right_square,
    snp_positions) {
  let left_y = border_height - coordinate_outer_buffer;
  let left = [track_x_position.toString(), left_y.toString()].join(',');

  let top_y = border_height - coordinate_outer_buffer - polygon_buffer +
      square_dims - buffer_btw_tracks;
  let _top = [track_x_position.toString(), top_y.toString()].join(',');

  let right_y = border_height - coordinate_outer_buffer - polygon_buffer +
      square_dims - buffer_btw_tracks;
  let right_x = track_x_position + square_dims;

  let right = [right_x.toString(), right_y.toString()].join(',');

  polygon_points = [left, _top, right].join(' ');

  var circle = track_svg.append('polygon')
		   .attr('points', polygon_points)
		   .attr('fill', 'green');
}

function add_bases_to_track(
    svg, snps, starting_x_pos, y_pos, square_dims, is_reference,
    reference_snps = [], d) {
  var position_data = [];
  var colors;

  // Get reference and trio snps at each position
  if (d != null) {
    for (const [key, value] of Object.entries(d['SNPS'])) {
      position_data.push(parseInt(key));
    }
    var Tooltip = d3.select('#tracks')
		      .append('div')
		      .style('opacity', 0)
		      .attr('class', 'tooltip')
		      .style('background-color', 'white')
		      .style('border', 'solid')
		      .style('border-width', '2px')
		      .style('border-radius', '5px')

    var color_base_mapping = {
      'G': d['COLOR']['g'],
      'C': d['COLOR']['c'],
      'T': d['COLOR']['t'],
      'A': d['COLOR']['a']
    };

    var base;
    var color;
    var num_snps = snps.length;
    var x_pos = starting_x_pos;
    i = 0
    for (base of snps) {
      if (is_reference == true) {
	// Fill reference bases with dark grey squares
	color = d['COLOR']['reference_track'];
      } else {
	// Check if reference_snps parameter passed, if
	// so assume reference_snps.length = snps.length
	// (also guaranteed by backend data
	// preprossessing)
	if (!(reference_snps.length == 0)) {
	  // If alternate allele, color according
	  // to base type
	  if (base != reference_snps[i]) {
	    color = color_base_mapping[base];
	  }
	  // Otherwise if base matches reference,
	  // color base same as reference
	  else {
	    color = d['COLOR']['base_matching_reference'];
	  }
	}
      }

      // Move to next base in reference sequence
      ++i;

      let halfway = square_dims / 2;

      // Append square base inside specific svg track
      var bases_rect = svg.append('rect')
			   .data(position_data)
			   .attr('class', 'bases')
			   .attr('x', x_pos)
			   .attr('y', y_pos)
			   .attr('height', square_dims)
			   .attr('width', square_dims)
			   .attr('fill', color)
			   .each(function(d, i) {});

      /* TODO: Add interactivity to each SNV position
			  .on('mouseover',
			      function(d) {
				      d3.selectAll('.bases')
					  .style('opacity',
	 '0.2') .filter(function() { return !this.classList
							      .contains(
								  'active')
					  })
				      d3.select(this)
					  .style('stroke',
	 '#4169E1') .attr('stroke-width', '2')
					  .style('opacity',
	 '1')
			      })
			  .on('mousemove',
			      function(d) {
				      // TODO
			      })
			  .on('mouseleave',
			      function(d) {
				      Tooltip.style('opacity',
	 0) d3.select(this).style('stroke', 'none')
				      d3.selectAll('.bases').style(
					  'opacity', '1')
			      })
			  .on('click', function(d, i) {
				  // TODO
				  console.log(d);
				  console.log(i);
			  });
				      */

      // Add base text inside the square
      svg.append('text')
	  .attr('x', x_pos + halfway)
	  .attr('y', y_pos + halfway)
	  .text(base)
	  // Center text char in square
	  .attr('text-anchor', 'middle')
	  .attr('dominant-baseline', 'central')
	  .style('fill', 'white')
	  .style('font-size', '20px');

      // Increment x_pos by width of square to place next
      // square
      x_pos += (square_dims + buffer_btw_bases);
    }
  }
}

// TODO: Old, remove
function draw_coordinate_line(track_svg, x_coordinate) {
  track_svg.append('line')
      .attr('x1', track_x_position + x_coordinate)
      .attr('x2', track_x_position + x_coordinate)
      .attr('y1', border_height - coordinate_outer_buffer)
      .attr(
	  'y2',
	  border_height - coordinate_outer_buffer + coordinate_track_height)
      .attr('stroke', '#dd760b');
}

function add_coordinate_track(
    track_svg, y_position, data, square_dims, container_width) {
  // New y position to update, and return
  var new_y = y_position;

  // Get all genomic positions
  var snp_positions = [];
  var scale_width = container_width - (track_x_position * 2);

  for (const [key, value] of Object.entries(data['SNPS'])) {
    snp_positions.push(parseInt(key));
  }
  //  Add reference at bottom of border
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', border_height - coordinate_outer_buffer)
      .attr('width', scale_width)
      .attr('height', coordinate_track_height)
      //.attr('fill', '#b2b2b2');
      .attr('fill', '#dadada');

  var zero = 0;
  var x_axis_height =
      border_height - coordinate_outer_buffer + coordinate_track_height;
  var x_axis_pos = [zero.toString(), x_axis_height.toString()].join(',');

  var x = d3.scaleLinear().domain([0, data['GENOME_SIZE']]).rangeRound([
    track_x_position, (container_width - track_x_position)
  ]);

  // Draw axis
  // TODO: Make vertical position a parameter
  track_svg.append('g')
      .attr(
	  'transform',
	  'translate(0,600)')  // vertical position
      .call(d3.axisBottom(x).tickValues(data['GENOMIC_RANGE']));

  //  Create x-axis label for coordinate track
  track_svg.append('text')
      .attr('class', 'x label')
      .attr('text-anchor', 'end')
      .attr('x', 280)
      .attr('y', border_height - 90)
      .attr('font-weight', 700)
      .style('font-size', '20px')
      .text('Genomic Coordinate');

  // Create x-axis label for gene region track
  track_svg.append('text')
      .attr('class', 'x label')
      .attr('text-anchor', 'end')
      .attr('x', 280)
      .attr('y', border_height - 35)
      .attr('font-weight', 700)
      .style('font-size', '20px')
      .text('Gene Annotations');

  var breakpoint_data = data['BREAKPOINTS'];

  /* Do not display breakpoint intervals on coordinate track for now
	  track_svg.append('rect')
	      .data([breakpoint_data])
	      .attr(
		  'width',
		  function(d) {
			  try {
				  return (
				      x(d['breakpoint1'].end) -
				      x(d['breakpoint1'].xpos))
			  } catch (error) {
				  return 0
			  }
		  })
	      .attr('height', coordinate_track_height)
	      .attr(
		  'x',
		  function(d) {
			  try {
				  return x(d['breakpoint1'].xpos)
			  } catch (error) {
				  return 0
			  }
		  })
	      .attr('y', border_height - coordinate_outer_buffer)
	      //.attr('fill', '#b2b2b2')
	      .attr('fill', '#dadada')

	      //.transition()
	      // Delay of the transition
	      //.delay(1000)
	      //.duration(3000)
	      .attr('fill', data['COLOR']['breakpoint_intervals']);

	  track_svg.append('rect')
	      .data([breakpoint_data])
	      .attr(
		  'width',
		  function(d) {
			  try {
				  return (
				      x(d['breakpoint2'].end) -
				      x(d['breakpoint2'].xpos))
			  } catch (error) {
				  return 0
			  }
		  })
	      .attr('height', coordinate_track_height)
	      .attr(
		  'x',
		  function(d) {
			  try {
				  return x(d['breakpoint2'].xpos)
			  } catch (error) {
				  return 0
			  }
		  })
	      .attr('y', border_height - coordinate_outer_buffer)
	      //.attr('fill', '#b2b2b2')
	      .attr('fill', '#dadada')

	      //.transition()
	      //.delay(1000)
	      //.duration(3000)

	      .attr('fill', data['COLOR']['breakpoint_intervals']);
  */

  // Drawing polygons
  const dot = track_svg.append('g')
		  .selectAll('dot')
		  .data(snp_positions)
		  .enter()
		  .append('circle')
		  .attr('cx', (d) => x(d))
		  .attr('cy', border_height - coordinate_outer_buffer)
		  .attr('r', 0.1)
		  .style('fill', 'darkblue')

  var lines =
      track_svg.selectAll('lines')
	  .data(snp_positions)
	  .enter()
	  .append('line')
	  .attr('class', 'lines')
	  .attr('x1', (d) => x(d))
	  .attr('x2', (d) => x(d))
	  .attr('y1', border_height - coordinate_outer_buffer)
	  .attr(
	      'y2',
	      border_height - coordinate_outer_buffer + coordinate_track_height)
	  .attr('stroke-width', '1.0')
	  // Starting color same as coordinate track
	  //.attr('stroke', '#b2b2b2')
	  .attr('stroke', '#dadada')

	  //.transition()
	  // Added a delay so the lines would appear in sequential
	  // increasing order
	  //.duration(function(d, i) {
	  // var delay = i * 200;
	  // return delay;
	  //})

	  // Fade in line posiiton color
	  // Speed slightly faster than matching polygons.
	  .attr('stroke', '#dd760b');  // Orange line for snp positions

  // Get informative site positions
  var info_sites = data['INFO_SITES'];

  var num = 0;
  var circle =
      track_svg.selectAll('polygon')
	  .data(snp_positions)
	  .enter()
	  .append('polygon')
	  .attr(
	      'points',
	      function(d, i) {
		var x_offset = x(d);
		let left_y = border_height - coordinate_outer_buffer;
		let left = [x_offset.toString(), left_y.toString()].join(',');

		let top_y = border_height - coordinate_outer_buffer -
		    polygon_buffer + square_dims - buffer_btw_tracks;
		// (square_dims*i) gives offset for
		// num square
		let top_x = track_x_position +
		    ((i * square_dims) + (i * buffer_btw_tracks));
		let _top = [top_x.toString(), top_y.toString()].join(',');

		let right_y = border_height - coordinate_outer_buffer -
		    polygon_buffer + square_dims - buffer_btw_tracks;
		let right_x = track_x_position +
		    (i * square_dims + (i * buffer_btw_tracks)) + square_dims;
		let right = [right_x.toString(), right_y.toString()].join(',');

		// Join all points
		// together in formatted
		// points string
		polygon_points = [left, _top, right].join(' ');


		return polygon_points;
	      })
	  .attr('fill', '#FFFFFF')

	  //.transition()
	  //.duration(function(d, i) {
	  // var delay = i * 200;
	  // return delay;
	  //})

	  .attr('fill', function(d, i) {
	    var color;
	    if (d.toString() in info_sites) {
	      var match = info_sites[d];
	      color = determine_informative(match, data['COLOR']);
	    } else {
	      // Otherwise not an informative site,
	      // don't highlight
	      color = data['COLOR']['non_informative_site'];
	    }
	    return color;
	  });

  let region_names = Object.keys(data['REGION_DATA']);
  let region_data = data['REGION_DATA'];
  draw_genomic_region(track_svg, region_names, region_data, x);

  // Display color legend left of visualization, below track labels
  display_legend(track_svg, data['COLOR']);

  return [track_svg, border_height - coordinate_outer_buffer];
}

function add_reference_track(
    track_svg, polygon_buffer, y_position, square_dims, reference_snps,
    snp_positions, d, container_width) {
  // New y position to update and return
  var new_y = y_position;
  var color = d['COLOR']['reference_track'];

  var scale_width = container_width - (track_x_position * 2);

  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - polygon_buffer - buffer_btw_tracks)
      .attr('width', scale_width)
      // The track height scales based on even paritioning of
      // square dimensions
      .attr('height', square_dims)
      .attr('fill', '#FFFFFF');

  track_svg.append('text')
      .attr('x', 0)
      .attr('y', track_x_position + square_dims)
      .style('font-size', '20px');

  var y_pos = new_y - polygon_buffer - buffer_btw_tracks;

  add_bases_to_track(
      track_svg, reference_snps, track_x_position, y_pos, square_dims, true,
      reference_snps, d);

  var top_line = 0;
  var left_square = 0;
  var right_square = 0;

  // Add label to left side of reference track
  var ref_label_text = 'Reference';
  var label_node_id = 'None';
  add_track_label(
      track_svg, new_y - polygon_buffer - buffer_btw_tracks, square_dims,
      ref_label_text, label_node_id, d);

  return [track_svg, new_y - buffer_btw_tracks - polygon_buffer - square_dims];
}

// TODO: Redundant, create templated function
function add_trio_track(
    track_svg, y_position, square_dims, d, container_width) {
  // New y position to update and return
  var new_y = y_position;
  var color = '#c6c6c6';
  var donor_snps = [];
  var recomb_snps = [];
  var acceptor_snps = [];
  var reference_snps = [];

  var scale_width = container_width - (track_x_position * 2);

  for (const [key, value] of Object.entries(d['SNPS'])) {
    donor_snps.push(value['Donor']);
    recomb_snps.push(value['Recomb']);
    acceptor_snps.push(value['Acceptor']);
    reference_snps.push(value['Reference']);
  }

  // Add donor track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', scale_width)
      .attr('height', square_dims)
      .attr('fill', '#FFFFFF');

  // Add snps to donor track
  add_bases_to_track(
      track_svg, donor_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);

  // Add label to donor track
  var donor_label_text = 'Donor';
  var label_node_id = d['NODE_IDS']['Donor'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, donor_label_text,
      label_node_id, d);

  new_y -= (square_dims + buffer_btw_tracks);

  // Add recombinant track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', track_width)
      .attr('height', square_dims)
      .attr('fill', '#FFFFFF');

  // Add snps to recomb track
  add_bases_to_track(
      track_svg, recomb_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);

  var recomb_label_text = 'Recombinant';
  var label_node_id = d['NODE_IDS']['Recomb'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, recomb_label_text,
      label_node_id, d);

  new_y -= (square_dims + buffer_btw_tracks);

  // Add acceptor track
  track_svg.append('rect')
      .attr('x', track_x_position)
      .attr('y', new_y - buffer_btw_tracks)
      .attr('width', track_width)
      .attr('height', square_dims)
      .attr('fill', '#FFFFFF');

  // Add snps to acceptor track
  add_bases_to_track(
      track_svg, acceptor_snps, track_x_position, new_y - buffer_btw_tracks,
      square_dims, false, reference_snps, d);


  var acceptor_label_text = 'Acceptor';
  var label_node_id = d['NODE_IDS']['Acceptor'];
  add_track_label(
      track_svg, new_y - buffer_btw_tracks, square_dims, acceptor_label_text,
      label_node_id, d);

  // TODO: Redundant
  var snp_positions = [];
  for (const [key, value] of Object.entries(d['SNPS'])) {
    snp_positions.push(key);
  }

  var num_snps = acceptor_snps.length;
  var label_width =
      (num_snps * square_dims + (num_snps - 1) * buffer_btw_bases) +
      track_x_position;

  var x = d3.scaleBand().domain(snp_positions).range([
    track_x_position, label_width
  ]);

  var info_sites = d['INFO_SITES'];
  var colors = d['COLOR'];

  track_svg.append('g')
      .attr('class', 'TopAxis')
      .data([snp_positions])
      .attr('transform', `translate(0,${new_y - buffer_btw_tracks - 5})`)
      .call(d3.axisTop(x))
      .selectAll('text')
      .style('text-anchor', 'start')
      .attr('dx', '1em')
      .attr('dy', '.2em')
      .style('font-size', '15px')
      .attr('transform', 'rotate(-65)')
      .style('fill', function(d, i) {
	var color;
	if (d.toString() in info_sites) {
	  var match = info_sites[d];
	  color = determine_informative(match, colors);
	} else {
	  // Otherwise not an informative site, don't
	  // highlight
	  color = colors['non_informative_site'];
	}
	return color;
      });
  track_svg.selectAll('.topAxis path').style('stroke', '#FFFFFF');
  /* TODO: Mouseover/click to column position labels
	  .on('mouseover',
	      function(d) {
		      d3.select(this).attr('fill', '#ff0000');
	      })
	      */

  // Set new y position (to add further tracks above if needed)
  new_y -= (square_dims + buffer_btw_tracks);

  return [track_svg, new_y];
}

function add_coordinate_axis(svg, margin, width, height) {
  // Create the scale
  var x = d3.scaleLinear().domain([0, 29903]).range([
    track_x_position, track_width + track_x_position
  ]);

  svg.append('g').attr('transform', 'translate(0,270)').call(d3.axisBottom(x));
}
