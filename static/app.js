window.onload = main;

function main() {
	// Border Constants
	var border = 1;
	var border_width = 1900;
	var border_height = 700;
	var init_track_width = 1750;

	var selection = d3.select('#tracks').append('div');

	// Create large SVG for the entire viz
	var svg = selection.append('svg')
		      .attr('width', border_width)
		      .attr('id', 'outer_SVG')
		      .attr('height', border_height);

	// Starting: y_position = border_height
	// Initialize a starting coordinate track
	init_coordinate_track(svg.append('svg'), init_track_width);

	track = graph().svg(svg).div(selection);

	// Download buttons
	const desc_button = document.querySelector('#download_all_descendants');
	const table_button = document.querySelector('#download_table');
	const tree_button = document.querySelector('#download_tree');
	const taxonium_button = document.querySelector('#download_taxonium');
	const search = document.querySelector('#search');

  var buttons = [desc_button, tree_button, taxonium_button, search];
  // Determine and setup production or local RIVET
  init_env(buttons);

	if (desc_button.style.visibility != 'hidden') {
		desc_button.addEventListener('click', () => {
			var url = download_all_descendants();
			window.location.href = url;
		}, false);
	}
	if (table_button) {
		table_button.addEventListener('click', () => {
			download_table();
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
	// TODO: Add visualization svg download button
}
