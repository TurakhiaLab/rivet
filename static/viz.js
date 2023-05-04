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
		    .attr('id', 'plot_title')
		    .attr('x', 300)
		    .attr('y', 120)
		    .attr('text-anchor', 'start')
		    .style('font-size', '30px')
		    .text(
			'Single-nucleotide variation in the recombinant and its parents');

		document.getElementById('download_svg').style.visibility =
		    'visible';
		// document.getElementById('copy_svg').style.visibility =
		//'visible';
		document.getElementById('next_button').style.visibility =
		    'visible';
		document.getElementById('previous_button').style.visibility =
		    'visible';

		// Disable overview side panel for local rivet for now
		if (d['COLOR']['environment'] == 'production') {
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
						data['overview']
						    ['recomb_lineage']);
					append_text(
					    overview,
					    'Recombinant Origin Date: ' +
						data['overview']
						    ['recomb_date']);
					append_text(
					    overview,
					    'Recombinant Between: ' +
						data['overview']
						    ['donor_lineage'] +
						' and ' +
						data['overview']
						    ['acceptor_lineage']);
					append_text(
					    overview,
					    'Number Sequences: ' +
						data['overview']['num_desc']
						    .toLocaleString());

					// Adding linebreaks for additional
					// buttons
					var linebreak =
					    document.createElement('br');
					linebreak.style.lineHeight = '14';
					overview.appendChild(linebreak);
				});
			});

			// TODO: Fix right offCanvas formatting of text
			/*
						// Append "More info" button in
			   overview section var overview_info_button =
						    document.createElement('button');
						overview_info_button.setAttribute(
						    'class', 'btn
			   btn-outline-primary');
						overview_info_button.setAttribute('id',
			   'info'); const info_btn_text =
						    document.createTextNode('More
			   Info');
						overview_info_button.appendChild(info_btn_text);
						overview.appendChild(overview_info_button);

						// Toggle offcanvas right
						// Handle next/prev result
			   button input if (overview_info_button) { var
			   overview_info = overview_info_button.onclick =
			   function() { var myOffcanvas =
									document.getElementById(
									    'off_canvas_right')
								    var
			   bsOffcanvas = new bootstrap.Offcanvas( myOffcanvas);
								    bsOffcanvas.show();
								    get_detailed_overview(overview,
			   d);
							    }
						}
						*/

			// Append "View UShER" button in overview section
			var overview_usher_button =
			    document.createElement('button');
			overview_usher_button.setAttribute(
			    'class', 'btn btn-outline-primary');
			overview_usher_button.setAttribute('id', 'view_usher');
			const usher_btn_text =
			    document.createTextNode('View UShER Tree');
			overview_usher_button.appendChild(usher_btn_text);
			overview.appendChild(overview_usher_button);

			const tooltip =
			    d3.select('#view_usher')
				.append('div')
				.style('position', 'absolute')
				.style('visibility', 'hidden')
				.style('padding', '15px')
				.style('background', 'rgba(0,0,0,0.6)')
				.style('border-radius', '5px')
				.style('color', 'white');

			if (overview_usher_button) {
				overview_usher_button.onclick = function() {
					view_usher_tree(d);
				};

				/*
	overview_usher_button.addEventListener(
	    'mouseover', function() {
		    usher_button_info_display(tooltip);
	    }, false);

	overview_usher_button.addEventListener(
	    'mouseout', function() {
		    usher_button_info_hide(tooltip);
	    }, false);
			*/
			}


			let private_table_select =
			    document.getElementById('full_table');
			if (private_table_select.hidden) {
				// Append "Tree View" button in overview section
				var overview_tree_button =
				    document.createElement('button');
				overview_tree_button.setAttribute(
				    'class', 'btn btn-outline-primary');
				overview_tree_button.setAttribute(
				    'id', 'view_tree');
				const tree_btn_text = document.createTextNode(
				    'View Taxonium Tree');
				overview_tree_button.appendChild(tree_btn_text);
				overview.appendChild(overview_tree_button);

				var view_tree_button =
				    document.querySelector('#view_tree');
				if (view_tree_button) {
					view_tree_button.onclick = function() {
						fetch('/get_tree_view', {
							method: 'POST',
							headers: {
								'Content-Type':
								    'application/json'
							},
							body: JSON.stringify(
							    d['NODE_IDS'])
						}).then(res => {
							res.json().then(data => {
								window.open(
								    data['url'],
								    '_blank');
							});
						});
					}
				}

				// Append "Show Defining Mutations" button in
				// overview section
			/*			
				var overview_mutations_button =
				    document.createElement('button');
				overview_mutations_button.setAttribute(
				    'class', 'btn btn-outline-primary');
				overview_mutations_button.setAttribute(
				    'id', 'show_mutations');
				const mutations_btn_text =
				    document.createTextNode(
					'Show Amino Acid Mutations');
				overview_mutations_button.appendChild(
				    mutations_btn_text);
				overview.appendChild(overview_mutations_button);
			}
			if (overview_mutations_button) {
				overview_mutations_button.onclick = function() {
					var nt_data = [];
					var nt_data = get_amino_acid_mutations(
					    d['NODE_IDS']['Recomb'], container,
					    y_position, snp_positions,
					    square_dims, num_snps, d);
				};
			*/
			}

			// Make summary visible
			overview.removeAttribute('hidden');
		}

		// Handle next/prev result button input
		if (next_button) {
			var next_element = next_button.onclick = function() {
				next_result(d['ID']);
			}
		}
		if (previous_button) {
			var previous_element =
			    previous_button.onclick = function() {
				    previous_result(d['ID'])
			    }
		}
		// Handle next/prev result arrow key input
		document.onkeydown =
		    function(e) {
			var keyCode = e.keyCode;
			if (keyCode == 37) {
				previous_element();
			} else if (keyCode == 39) {
				next_element();
			}
		}

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
