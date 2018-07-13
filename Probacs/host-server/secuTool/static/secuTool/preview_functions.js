var button_id = 100

function addflag(flag) {
	var id = "#" + flag
	if ($(id).hasClass("chosen")) {
		$(id).removeClass("chosen")
	} else {
		$(id).addClass("chosen")
	}
}

function delflag(flag) {
	var button_id = '#' + flag + "z"
	var flag = $(button_id).text().trim()
	var parent_id = $(button_id).parent().attr("id")
	var input_id = '#input' + parent_id.substring(parent_id.length - 1, parent_id.length)
	var cnt = Number($(button_id).parent().children(".cnter").text()) - 1
	if (cnt === 0) {
		$(button_id).parent().remove()
		$(input_id).remove()
	} else {
		var form_value = $(input_id).attr("value").replace(flag, "")
		$(button_id).parent().children(".cnter").text(cnt)
		$(input_id).attr({ "value": form_value })
		$(button_id).remove()
	}
}

function selectall() {
	$('.row-button').each(function () {
		$(this).addClass('chosen')
	})
}

function deselectall() {
	$('.row-button').each(function () {
		$(this).removeClass('chosen')
	})
}

function confirmgroup() {
	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
	var buttons = ""
	var flags = ""
	var flag_number = 0
	$('.button-check-box').each(function () {
		if ($(this).hasClass("chosen")) {
			buttons += '<button class="btn btn-light btn-sm" id="' + $(this).attr("id").trim() + "z" + '" >'
			// '" onclick="delflag(\'' + $(this).attr("id").trim() + '\')">' 
				+ $(this).parent().text().trim() + '</button>'
			flags += $(this).parent().text().trim() + " "
			$(this).removeClass("chosen")
			flag_number += 1
		}
	})
	if (flag_number === 0) return
	var form_item = '<div style="visibility: hidden" id="' + 'group">' + flags + '</div>'
	var group_item = '<div id="flag-group' + '"> <p style="display: inline-block">group: </p>' + buttons +
		'<p hidden class = "cnter">' + flag_number + '</p>' + '</div>'
	$('#groups').prepend(group_item)
	$('#group-handin').prepend(form_item)
}

function clearall() {
	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
}

function add_row() {
	if ($('#group').text().trim() === "") return
	flags = $('#group').text().trim().split(" ")
	flags = flags.join(", ")
	new_row = ""
	message = ""
	var selected = 0, max_row = 0
	$('.row-button').each(function () {
		var row = parseInt($(this).closest('tr').find('td.id').text())
		max_row = Math.max(row, max_row)
	})
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {
			max_row++
			//append a new row
			new_row += '<tr bgcolor="#F0F8FF">' +
				'<td><button class="row-button" id="r' + button_id + '" onclick="addflag(\'r' + button_id + '\')"></button></div></td>' +
				'<td class="id">' + max_row + '</td>' +
				'<td class="os">' + $(this).closest('tr').find('td.os').text() + '</td>' +
				'<td class="compiler">' + $(this).closest('tr').find('td.compiler').text() + '</td>' +
				'<td class="profile">' + $(this).closest('tr').find('td.profile').text() + '</td>' +
				'<td class="flag new_flag" contenteditable="true">' + $(this).closest('tr').find('td.flag').text() + ", " + flags + '</td>' +
				'<td class="username">' + $(this).closest('tr').find('td.username').text() + '</td>' +
				'<td class="tags">' + $(this).closest('tr').find('td.tags').text() + '</td>' +
				'<td><button class="btn btn-light btn-sm" onclick="delete_row(\'r' + button_id + '\')">delete</button></td>'
				+ '</tr>'
			selected++
			button_id++
			$(this).removeClass("chosen")
			message += $(this).closest('tr').find('td.id').text() + ": (" + $(this).closest('tr').find('td.os').text() + "; " +
				$(this).closest('tr').find('td.compiler').text() + "; " + $(this).closest('tr').find('td.profile').text() + "; " +
				$(this).closest('tr').find('td.flag').text() + "; " + $(this).closest('tr').find('td.username').text() + ") <br>"
		}
	})
	if (selected === 0) return
	$('#preview-list').append(new_row)

	logtext = 'You added ' + $("#group").text() + ' to task ' + message
	document.getElementById("log").innerHTML += logtext

	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
	edit_flags('.new_flag')
}

function delete_row(row) {
	var id = '#' + row
	message = $(id).closest('tr').find('td.id').text() + ": (" + $(id).closest('tr').find('td.os').text() + "; " +
		$(id).closest('tr').find('td.compiler').text() + "; " + $(id).closest('tr').find('td.profile').text() + "; " +
		$(id).closest('tr').find('td.flag').text() + "; " + $(id).closest('tr').find('td.username').text() + ")"
	$(id).closest('tr').remove()
	logtext = 'You deleted task ' + message + '<br>'
	document.getElementById("log").innerHTML += logtext
}

function edit_flags(flag) {
	$(flag).focus(function () {
		original = $(this).text()
	});
	$(flag).blur(function () {
		updated = $(this).text()
		if (original != updated) {
			id = $(this).closest('tr').find('td.id').text()
			logtext = 'You modified task ' + id + ': from "' + original + '" to "' + updated + '"<br>'
			document.getElementById("log").innerHTML += logtext
		}
	});
}

function compile() {
	var param = []
	var cnt = 0
	var set = new Set()
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {
			var obj = {}
			obj['os'] = $(this).closest('tr').find('td.os').text()
			obj['compiler'] = $(this).closest('tr').find('td.compiler').text()
			obj['profile'] = $(this).closest('tr').find('td.profile').text()
			var flag = $(this).closest('tr').find('td.flag').text()
			if(set.has(flag)) {
				return
			}
			set.add(flag)
			obj['flag'] = flag
			obj['username'] = $(this).closest('tr').find('td.username').text()
			obj['tags'] = $(this).closest('tr').find('td.tags').text()
			param.push(obj)
			cnt++
		}
	})
	if (cnt === 0) return
	console.log(param)
	$.ajax({
		type: 'POST',
		url: "/paramUpload",
		dataType: "json",
		data: {
			taskid: $('#taskid').text().trim(),
			taskCount: cnt,
			tasks: param,
		},
		success: function (response) {
			console.log(response.taskid)
			$('#redirect').click()
		}
	});
}

function display_flags() {
	var json_flags = $('#json_flags').text()
	if (json_flags === "" || json_flags === null) return
	var plist = JSON.parse(json_flags)
	var message = ''
	for (p in plist) {
		message += '<div class="js-debug">'
		message += '<button class="button-check-box" id=flag' + p + ' onclick="addflag(this.id)"></button> ' + plist[p] + '</div>'
	}
	$('#display_flags').append(message)
}

function main_page() {
	window.location.href = '/test';
}

function onload_wrapper() {
	display_flags()
	edit_flags('.flag')
}

window.onload = onload_wrapper;