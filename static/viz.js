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

		document.getElementById('download_svg').style.visibility =
		    'visible';
		// document.getElementById('copy_svg').style.visibility =
		//'visible';

		// Summary side panel generated for each selected row
		const overview = document.getElementById('summary');
		// Clear any previous text elements from overview div
		overview.textContent = '';

		// Append overview header
		var overview_header = document.createElement('h3');
		const header_text = document.createTextNode('Overview');
		overview_header.setAttribute('id', 'overview_header');
		overview_header.appendChild(header_text);
		overview.appendChild(overview_header);

		// Get data from table for each of these fields
		fetch('/get_overview', {
			method: 'POST',
			headers: {'Content-Type': 'application/json'},
			body: JSON.stringify({'id': d['ID']})
		}).then(res => {
			res.json().then(data => {
				append_text(
				    overview,
				    'Recombinant Node ID: ' +
					d['NODE_IDS']['Recomb']);
				append_text(
				    overview,
				    'Current Recombinant Lineage Designation: ' +
					data['overview']['recomb_lineage']);
				append_text(
				    overview,
				    'Recombinant Origin Date: ' +
					data['overview']['recomb_date']);
				append_text(
				    overview,
				    'Recombinant Between: ' +
					data['overview']['donor_lineage'] +
					' and ' +
					data['overview']['acceptor_lineage']);

				// TODO: Add
				/*
								append_text(overview,
				   'Earliest Sequence: '); append_text(overview,
				   'Most Recent Sequence: '); append_text(
								    overview,
				   'Countries Circulating: ');
										*/

				append_text(overview, 'QC Flags: ');
				append_list(
				    overview, data['overview']['qc_flags']);

				// TODO: Add
				// append_text(overview, 'Defining Mutations:
				// ');
			});
		});

		// Append "Tree View" button in overview section
		var overview_tree_button = document.createElement('button');
		overview_tree_button.setAttribute(
		    'class', 'btn btn-outline-primary');
		overview_tree_button.setAttribute('id', 'view_tree');
		const tree_btn_text = document.createTextNode('View Taxonium');
		overview_tree_button.appendChild(tree_btn_text);
		overview.appendChild(overview_tree_button);

		var view_tree_button = document.querySelector('#view_tree');
		if (view_tree_button) {
			view_tree_button.onclick = function() {
				fetch('/get_tree_view', {
					method: 'POST',
					headers: {
						'Content-Type':
						    'application/json'
					},
					body: JSON.stringify(d['NODE_IDS'])
				}).then(res => {
					res.json().then(data => {
						window.open(
						    data['url'], '_blank');
					});
				});
			}
		}

		// Make summary visible
		overview.removeAttribute('hidden');


		if (download_svg) {
			var inner = document.getElementById('inner_SVG');
			download_svg.onclick = function() {
				download_snv_plot(
				    inner, d['NODE_IDS']['Recomb']);
			};
		}

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
