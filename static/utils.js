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

function display_descendants(label_node_id) {
	fetch('/get_descendants', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({node: label_node_id})
	}).then(res => {
		res.json().then(data => {
			// First remove previously fetched list of descendants
			d3.select('#desc').remove();

			// Toggle offcanvas left
			var myOffcanvas =
			    document.getElementById('off_canvas_left')
			var bsOffcanvas = new bootstrap.Offcanvas(myOffcanvas)
			bsOffcanvas.show()

			// Get descendants data and format 1 per line
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

			// Write node descendants to file on button click
			var file_name = label_node_id + '_descendants.txt';
			var obj = ['hi1\tresults2\n'];
			var obj1 = format_txt(data);
			console.log(obj1);

			const desc_button =
			    document.querySelector('#download_descendants');
			// Listen for download
			if (desc_button) {
				console.log('Got inside!');
				desc_button.addEventListener(
				    'click',
				    () => {serialize_object(file_name, obj1)},
				    false);
			}
		});
	});
}
