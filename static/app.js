window.onload = main;

function main() {
	// Border Constants
	var border = 1;
	var border_width = 1400;
	var border_height = 700;

	var selection = d3.select('#tracks').append('div');

	// Create large SVG for the entire viz
	var svg = selection.append('svg')
		      .attr('width', border_width)
		      .attr('height', border_height);

	// Starting: y_position = border_height
	init_coordinate_track(svg.append('svg'), border_height);

	// Add legend for visualization
	var legend = d3.select('#legend').append('div');

	// Create small SVG for the viz legend
	var legend_svg =
	    legend.append('svg').attr('width', 400).attr('height', 600);

	track = graph().svg(svg).legend(legend_svg);

	// Download buttons
	const desc_button = document.querySelector('#download_all_descendants');
	const table_button = document.querySelector('#download_table');
	if (desc_button) {
		desc_button.addEventListener('click', () => {
			download_all_descendants();
		}, false);
	}
	if (table_button) {
		table_button.addEventListener('click', () => {
			download_table();
		}, false);
	}
	// TODO: Add visualization svg download button
}
