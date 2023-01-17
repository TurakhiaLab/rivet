/* Utility functions */

function format_txt(data) {
	var obj = '';
	for (let i = 0; i < data.length; ++i) {
		if (i == data.length - 1) {
			obj += data[i];
			break;
		}
		obj += (data[i] + '\n');
	}
	// Return string obj as array
	return [obj];
}

function serialize_object(file_name, obj) {
	// Create download file
	const file = new File(obj, file_name);

	const link = document.createElement('a');
	link.style.display = 'none';
	link.href = URL.createObjectURL(file);
	link.download = file.name;

	document.body.appendChild(link);
	link.click();

	setTimeout(() => {
		URL.revokeObjectURL(link.href);
		link.parentNode.removeChild(link);
	}, 0);
}

function format_descedants(data) {
	var string = '';
	for (const element of data) {
		string += element;
		string += '<br>';
	}
	string += '<br>'
	return string;
}

function format_tsv(data) {
	var obj = '';
	for (let i = 0; i < data.length; ++i) {
		for (let j = 0; j < data[i].length; ++j) {
			if (j == data[i].length - 1) {
				obj += data[i][j];
				obj += '\n';
			} else {
				obj += data[i][j];
				obj += '\t';
			}
		}
	}
	// Return string obj as array
	return [obj];
}

function download_all_descendants() {
	fetch('/get_all_descendants', {
		method: 'POST',
		headers: {'Content-Type': 'text/plain'},
		body: {download: 'all_descendants'}
	}).then(res => {});
	return '/get_all_descendants';
}

function download_table() {
	fetch('/download_table', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({download: 'table'})
	}).then(res => {
		res.json().then(data => {
			var file_name = 'recombination_results.txt';
			formatted_data = format_tsv(data);
			serialize_object(file_name, formatted_data);
		});
	});
}

function display_descendants(label_node_id) {
	if (label_node_id == 'None') {
		return;
	}

	fetch('/get_descendants', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({node: label_node_id})
	}).then(res => {
		res.json().then(data => {
			// First remove previously fetched list
			// of descendants
			d3.select('#desc').remove();

			// Toggle offcanvas left
			var myOffcanvas =
			    document.getElementById('off_canvas_left')
			var bsOffcanvas = new bootstrap.Offcanvas(myOffcanvas)
			bsOffcanvas.show()

			// Get descendants data and format 1 per
			// line
			var desc_string = format_descedants(data);

			var num_des = data.length;
			// Set text formatting size
			var font_size = 14;

			var selection = d3.select('#off_canvas_left_body')
					    .append('p')
					    .attr('id', 'desc');

			const paragraph = d3.select('#desc');
			paragraph.append('foreignObject')
			    .append('xhtml:p')
			    .attr('font-size', font_size)
			    .html(desc_string);

			const desc_button =
			    document.querySelector('#download_descendants');
			if (desc_button) {
				desc_button.addEventListener('click', () => {
					window.location.href =
					    '/download_select_descendants?id=' +
					    label_node_id;
				}, false);
			}
		});
	});
}

function download_tree() {
	fetch('/download_mat', {
		method: 'POST',
	}).then(res => {
		res.json().then(data => {
			// Format: year-month-date
			var date = data['date'];
			// Format: "public-year-month-date.all.masked.pb.gz"
			var mat = 'public-' + date + '.all.masked.pb.gz';
			date = date.split('-').join('/');
			date = date + '/' + mat;
			//  Format:
			//  'http://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/year/month/date/';
			var mat_url =
			    'http://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/' +
			    date;
			window.location.href = mat_url;
		});
	});
}

function determine_informative(match, colors) {
	// Matches the acceptor
	if (match == 'A') {
		return colors['recomb_match_acceptor'];
	} else {
		// Matches the donor
		return colors['recomb_match_donor'];
	}
}

function display_legend(svg, colors) {
	var items = [
		'Recombinant matches acceptor', 'Recombinant matches donor',
		'Non-Recombinant-Informative'
	];
	//'Breakpoint Intervals'

	var color_range = [
		colors['recomb_match_acceptor'], colors['recomb_match_donor'],
		colors['non_informative_site']
	];
	var legend_square_size = 30;
	var num_items = 3;

	const legend_item_starting_height = 450;
	var legend_item_h = legend_item_starting_height;

	// Add legend row color square
	svg.selectAll('squares')
	    .data(color_range)
	    .enter()
	    .append('rect')
	    .attr('x', 10)
	    .attr(
		'y',
		function(d, i) {
			if (i == 0) {
				return legend_item_starting_height;
			}
			return legend_item_h += legend_square_size + 5;
		})
	    .attr('width', legend_square_size)
	    .attr('height', legend_square_size)
	    .attr('fill', d => d);

	// Reset item height to starting height
	legend_item_h = legend_item_starting_height;

	// Add legend row label
	svg.selectAll('labels')
	    .data(items)
	    .enter()
	    .append('text')
	    .attr('x', 45)
	    .attr(
		'y',
		function(d, i) {
			if (i == 0) {
				return legend_item_starting_height +
				    (legend_square_size / 2);
			}
			legend_item_h += legend_square_size + 5;
			return legend_item_h + (legend_square_size / 2);
		})
	    .attr(
		'fill',
		function(d, i) {
			return color_range[i];
		})
	    .text(d => d)
	    .attr('text-anchor', 'left')
	    .style('alignment-baseline', 'middle');
}

