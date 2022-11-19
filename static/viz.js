function graph() {
	var svg;

	// Set constants for tracks
	var border_color = 'black';
	const buffer_btw_tracks = 5;
	const buffer_btw_bases = 5;
	const outer_buffer = 50;  // Enough to be larger than height of track
	const label_halfway = 20;
	const polygon_buffer = 150;
	const trio_block_buffer = 25;
	const track_height = 25;
	const track_width = 1200;
	const track_x_position = 150;
	const track_y_position = border_height;	 // Plus some offset upwards
	const num_tracks = 0;

	const margin = {top: 100, right: 100, bottom: 100, left: 100},
	      width = track_width
	height = border_height - outer_buffer;


	function track(d) {
		// Clear previous visualization elements
		svg.selectAll('svg').remove();
		svg.selectAll('rect').remove();
		svg.selectAll('text').remove();

		var y_position = border_height;
		var snp_positions = [];
		var reference_snps = [];

		// Get reference and trio snps at each position
		console.log(d['SNPS']);
		for (const [key, value] of Object.entries(d['SNPS'])) {
			snp_positions.push(parseInt(key));
			reference_snps.push(value['Reference']);
		}
		var num_snps = reference_snps.length;

		if (num_snps == 0) {
			// Error handle zero SNPS
			handle_zero_snps(svg);
			return;
		}
		// Less than 15 snps, tracks and bases will have fixed size
		if (num_snps < 15) {
			var small_track_width = track_width / 2;

			let square_dims = 50;

			var coordinate_track_list = add_small_coordinate_track(
			    svg.append('svg'), y_position, d, square_dims);

			var coordinate_track = coordinate_track_list[0];
			y_position = coordinate_track_list[1];

			// Init reference track
			var reference_track_list = add_small_reference_track(
			    svg.append('svg'), polygon_buffer, y_position,
			    square_dims, reference_snps, snp_positions, d);

			var reference_track = reference_track_list[0];
			y_position = reference_track_list[1];

			// Add trio tracks
			var trio1_list = add_small_trio_track(
			    svg.append('svg'), y_position, square_dims, d);

			var trio1_track = trio1_list[0];
			y_position = trio1_list[1];
		}
		// TODO: Add a check for snps greater than 50 or 60.
		// Add visualization scrolling for this
		// Then eventhing in-b/w is handled by autoscaling

		if (num_snps >= 15) {
			let square_dims =
			    ((track_width -
			      (buffer_btw_bases * (num_snps - 1))) /
			     num_snps);

			var coordinate_track_list = add_coordinate_track(
			    svg.append('svg'), y_position, d, square_dims);

			var coordinate_track = coordinate_track_list[0];
			y_position = coordinate_track_list[1];

			var reference_track_list = add_reference_track(
			    svg.append('svg'), polygon_buffer, y_position,
			    square_dims, reference_snps, snp_positions, d);

			var reference_track = reference_track_list[0];
			y_position = reference_track_list[1];

			var trio1_list = add_trio_track(
			    svg.append('svg'), y_position, square_dims, d);

			var trio1_track = trio1_list[0];
			y_position = trio1_list[1];
		}
	}

	track.svg = function(value) {
		svg = value;
		return track;
	};

	return track;
}
