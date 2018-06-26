var groupNumber = 0
var button_id = 100

function addflag(flag) {
	var id = "#" + flag
	if ($(id).hasClass("chosen")) {
		$(id).removeClass("chosen")
	} else {
		$(id).addClass("chosen")
	}
}

function selectall(){
	$('.row-button').each(function () {
		$(this).addClass('chosen')
	})
}

function deselectall(){
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
			// '" onclick="delflag(\'' +$(this).attr("id").trim() + '\')">' 
				+ $(this).parent().text().trim() + '</button>'
			flags += $(this).parent().text().trim() + " "
			$(this).removeClass("chosen")
			flag_number += 1
		}
	})
	if (flag_number === 0) return
	// groupNumber += 1
	var form_item = '<div style="visibility: hidden" id="' + 'group">' + flags + '</div>'
	var group_item = '<div id="flag-group' + '"> <p style="display: inline-block">group: </p>' + buttons +
		'<p hidden class = "cnter">' + flag_number + '</p>' + '</div>'
	$('#groups').prepend(group_item)
	$('#group-handin').prepend(form_item)
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

function clearall() {
	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
}

function add_row() {
	if($('#group').text().trim() === "") return
	flags = $('#group').text().trim().split(" ")
	console.log(flags)
	// console.log(flags) 
	flags = flags.join(",")
	new_row = ""
	var selected = 0
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {
			//append a new row
			var os = $(this).closest('tr').find('td.os').text()
			console.log(os)
			new_row += '<tr>'+
			'<td><button class="row-button" id="r'+button_id+'" onclick="addflag(\'r'+button_id+'\')"></button></div></td>'+
			'<td class="os">'+$(this).closest('tr').find('td.os').text()+'</td>'+
			'<td class="compiler">'+$(this).closest('tr').find('td.compiler').text()+'</td>'+
			'<td class="profile">'+$(this).closest('tr').find('td.profile').text()+'</td>'+
			'<td class="flag">'+$(this).closest('tr').find('td.flag').text()+","+flags+'</td>'+
			'<td class="username">'+$(this).closest('tr').find('td.username').text()+'</td>'+
			'<td class="tags">'+$(this).closest('tr').find('td.tags').text()+'</td>'+
			'<td><button class="btn btn-light btn-sm" onclick="delete_row(\'r'+button_id+'\')">delete</button></td>'
			+'</tr>'
			button_id++;
			$(this).removeClass("chosen")
			selected++
		}
	})
	if(selected === 0) return
	$('#preview-list').append(new_row)
	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
}

function delete_row(row) {
	var id = '#'+row
	$(id).closest('tr').remove()
}

$("#myform").submit(function () {
	alert("AAAAA")
	var checked = $('#myform input[type="checkbox"]:checked').length > 0;
	if (!checked) {
		alert("Please check at least one checkbox");
		return false;
	}
});

$('#compile').submit(function(e){
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {

		}
	})
	$("#compile input:submit").click();
})

function compile() {
	var param = []
	var cnt = 0
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {
			var obj = {}
			obj['os'] = $(this).closest('tr').find('td.os').text()
			obj['compiler'] = $(this).closest('tr').find('td.compiler').text()
			obj['profile'] = $(this).closest('tr').find('td.profile').text()
			obj['flag'] = $(this).closest('tr').find('td.flag').text()
			obj['username'] = $(this).closest('tr').find('td.username').text()
			obj['tags'] = $(this).closest('tr').find('td.tags').text()
			// console.log(obj)
			param.push(obj)
			cnt++
		}
	})
	if(cnt === 0) return
	console.log(param)
	$.ajax({
		type: 'POST',
		url: "/paramUpload",
        dataType : "json",
        data: {
        	taskid: $('#taskid').text().trim(),
        	taskCount: cnt,
        	tasks: param,
        },
      	success:  function(response) {
      		console.log(response.taskid)
      		$('#redirect').click()
      	}  
	});
}