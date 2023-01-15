function graph() {
	var svg;
	var div;
	var legend;

	// Set constants for tracks
	var border_color = 'black';
	const buffer_btw_tracks = 5;
	const buffer_btw_bases = 5;
	const outer_buffer = 50;  // Enough to be larger than height of track
	const label_halfway = 20;
	const polygon_buffer = 150;
	const trio_block_buffer = 25;
	const track_height = 25;
	const track_width = 1750;
	const track_x_position = 300;
	const track_y_position = border_height;	 // Plus some offset upwards
	const num_tracks = 0;

	const margin = {top: 100, right: 100, bottom: 100, left: 100},
	      width = track_width
	height = border_height - outer_buffer;

	function track(d) {
		// Clear previous track visualization elements
		div.selectAll('svg').remove();

		var y_position = border_height;
		var snp_positions = [];
		var reference_snps = [];

		// Get reference and trio snps at each position
		for (const [key, value] of Object.entries(d['SNPS'])) {
			snp_positions.push(parseInt(key));
			reference_snps.push(value['Reference']);
		}
		var num_snps = reference_snps.length;
		var fixed_square_dims = 30;
		var medium_track_width = track_width;
		var square_dims;
		var container_width;

		// Error handle zero SNPS
		if (num_snps == 0) {
			handle_zero_snps(div);
			return;
		}
		// Less than 20 snps, scale down medium track size, make base
		// sizes slightly larger
		if (num_snps < 20) {
			container_width = medium_track_width;
			square_dims = 40;
		}
		// Between 20-40 snps: Keep container width and base size fixed
		if (num_snps >= 20 && num_snps <= 40) {
			square_dims = 30;
			container_width = medium_track_width;
		}
		// >40 snps: container width becomes variable,
		// snp base sizes fixed
		if (num_snps > 40) {
			container_width = (buffer_btw_bases * (num_snps - 1)) +
			    (num_snps * fixed_square_dims) + track_x_position;
			square_dims = fixed_square_dims;
		}

		// Variable svg container width based on
		// number of snps
		var container = div.append('svg')
				    .attr('id', 'inner_SVG')
				    .attr('width', container_width)
				    .attr('height', 700);

		// Add title to SNP visualization plot
		container.append('text')
		    .attr('x', 300)
		    .attr('y', 150)
		    .attr('text-anchor', 'start')
		    .style('font-size', '30px')
		    .text(
			'Single-nucleotide variation in the recombinant and its parents');

		var coordinate_track_list = add_coordinate_track(
		    container, y_position, d, square_dims, container_width);

		var coordinate_track = coordinate_track_list[0];
		y_position = coordinate_track_list[1];

		var reference_track_list = add_reference_track(
		    container, polygon_buffer, y_position, square_dims,
		    reference_snps, snp_positions, d, container_width);

		var reference_track = reference_track_list[0];
		y_position = reference_track_list[1];

		var trio_list = add_trio_track(
		    container, y_position, square_dims, d, container_width);

		var trio_track = trio_list[0];
		y_position = trio_list[1];
	}

	track.svg = function(value) {
		svg = value;
		return track;
	};
	track.div = function(value) {
		div = value;
		return track;
	};

	track.legend = function(value) {
		legend = value;
		return track;
	};

	return track;
}
