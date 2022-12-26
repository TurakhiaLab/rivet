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
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({download: 'all_descendants'})
	}).then(res => {
		res.json().then(data => {
			var file_name = 'descendants.txt';
			formatted_data = format_tsv(data);
			serialize_object(file_name, formatted_data);
		});
	});
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
			    .style('font-weight', 'bold')
			    .html(desc_string);

			// Write node descendants to file on
			// button click
			var file_name = label_node_id + '_descendants.txt';
			var obj = ['hi1\tresults2\n'];
			var obj1 = format_txt(data);

			const desc_button =
			    document.querySelector('#download_descendants');
			// Listen for download
			if (desc_button) {
				desc_button.addEventListener(
				    'click',
				    () => {serialize_object(file_name, obj1)},
				    false);
			}
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
		'Non-Recombinant-Informative SNP', 'Breakpoint Intervals'
	];
	var color_range = [
		colors['recomb_match_acceptor'], colors['recomb_match_donor'],
		colors['non_informative_site'], colors['breakpoint_intervals']
	];
	var scale = d3.scaleOrdinal().domain(items).range(color_range);

	const legend_square_size = 30
	svg.selectAll('squares')
	    .data(items)
	    .enter()
	    .append('rect')
	    .attr('x', 10)
	    .attr(
		'y',
		function(d, i) {
			return 300 + i * (legend_square_size + 5)
		})
	    .attr('width', legend_square_size)
	    .attr('height', legend_square_size)
	    .style('fill', function(d) {
		    return scale(d)
	    })

	svg.selectAll('labels')
	    .data(items)
	    .enter()
	    .append('text')
	    .attr('x', 10 + legend_square_size * 1.2)
	    .attr(
		'y',
		function(d, i) {
			return 300 + i * (legend_square_size + 5) +
			    (legend_square_size / 2)
		})
	    .style(
		'fill',
		function(d) {
			return scale(d)
		})
	    .text(function(d) {
		    return d
	    })
	    .attr('text-anchor', 'left')
	    .style('alignment-baseline', 'middle')
}
