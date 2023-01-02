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
	if (desc_button) {
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
	// TODO: Add visualization svg download button
}
