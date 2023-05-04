window.onload = main;

function main() {
	// Border Constants
	var border = 1;
	var border_width = 1900;
	var border_height = 700;
	var init_track_width = 1750;
	// var init_track_width = 1250;

	var selection = d3.select('#tracks').append('div');

	// Create large SVG for the entire viz
	var svg = selection.append('svg')
		      .attr('width', border_width)
		      .attr('id', 'outer_SVG')
		      .attr('height', border_height);

	// Starting: y_position = border_height
	// Initialize a starting coordinate track
	init_coordinate_track(svg.append('svg'), init_track_width);

	// SNV plot svg download and copy buttons setup
	/*
var copy_snv_button =
create_button('copy_svg', 'Copy SNV Plot', 1200, 280);
*/
	if (document.querySelector('#table_title')) {
		// Show results table title and select tree buttons
		document.querySelector('#table_title')
		    .removeAttribute('hidden');
	}

	var download_snv_button =
	    create_button('download_svg', 'Download SNV', 1250, 280);
	var download_svg = document.querySelector('#download_svg');
	// var copy_svg = document.querySelector('#copy_svg');
	download_svg.style.visibility = 'hidden';
	// copy_svg.style.visibility = 'hidden';

	var next_button = create_button('next_button', 'Next', 1700, 280);
	var previous_button =
	    create_button('previous_button', 'Previous', 1600, 280);
	previous_button.style.visibility = 'hidden';
	next_button.style.visibility = 'hidden';

	// Create SNV plot visualization
	track = graph().svg(svg).div(selection);

	// Download buttons
	const desc_button = document.querySelector('#download_all_descendants');
	const full_tree_desc_button =
	    document.querySelector('#full_table_download_all_descendants');
	const table_button = document.querySelector('#download_table');
	const full_table_button =
	    document.querySelector('#download_full_table');
	const tree_button = document.querySelector('#download_tree');
	const taxonium_button = document.querySelector('#download_taxonium');
	const search = document.querySelector('#search');

	// Left and right arrow keys reserved for scrolling between results
	window.addEventListener('keydown', function(e) {
		if (['ArrowLeft', 'ArrowRight'].indexOf(e.code) > -1) {
			e.preventDefault();
		}
	}, false);

	var buttons = [desc_button, tree_button, taxonium_button, search];
	// Determine and setup production or local RIVET
	init_env(buttons);

	if (desc_button.style.visibility != 'hidden') {
		desc_button.addEventListener('click', () => {
			var url = download_all_descendants();
			window.location.href = url;
		}, false);
	}
	if (full_tree_desc_button) {
		if (full_tree_desc_button.style.visibility != 'hidden') {
			full_tree_desc_button.addEventListener('click', () => {
				// TODO: Get working for full tree
				var url = download_all_descendants();
				window.location.href = url;
			}, false);
		}
	}

	if (table_button) {
		table_button.addEventListener('click', () => {
			download_table('public');
		}, false);
	}
	if (full_table_button) {
		full_table_button.addEventListener('click', () => {
			// Downloading full tree results table
			download_table('full');
		}, false);
	}

	if (tree_button.style.visibility != 'hidden') {
		tree_button.addEventListener('click', () => {
			download_tree();
		}, false);
	}
	if (taxonium_button.style.visibility != 'hidden') {
		taxonium_button.addEventListener('click', () => {
			download_taxonium();
		}, false);
	}
}
