var groupNumber = 0
var button_id = 100
var interval = 1000;
var finished_status = false
var text = ""

function addflag(flag) {
	var id = "#" + flag
	if ($(id).hasClass("chosen")) {
		$(id).removeClass("chosen")
	} else {
		$(id).addClass("chosen")
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
	if ($('#group').text().trim() === "") return
	flags = $('#group').text().trim().split(" ")
	flags = flags.join(", ")
	new_row = ""
	message = ""
	var selected = 0
	$('.row-button').each(function () {
		if ($(this).hasClass("chosen")) {
			//append a new row
			var os = $(this).closest('tr').find('td.os').text()
			console.log(os)
			new_row += '<tr bgcolor="#F0F8FF">' +
				'<td><button class="row-button" id="r' + button_id + '" onclick="addflag(\'r' + button_id + '\')"></button></div></td>' +
				'<td class="os">' + $(this).closest('tr').find('td.os').text() + '</td>' +
				'<td class="compiler">' + $(this).closest('tr').find('td.compiler').text() + '</td>' +
				'<td class="profile">' + $(this).closest('tr').find('td.profile').text() + '</td>' +
				'<td class="flag" contenteditable="true">' + $(this).closest('tr').find('td.flag').text() + ", " + flags + '</td>' +
				'<td class="username">' + $(this).closest('tr').find('td.username').text() + '</td>' +
				'<td class="tags">' + $(this).closest('tr').find('td.tags').text() + '</td>' +
				'<td><button class="btn btn-light btn-sm" onclick="delete_row(\'r' + button_id + '\')">delete</button></td>'
				+ '</tr>'
			button_id++;
			$(this).removeClass("chosen")
			selected++
			message += $(this).closest('tr').find('td.os').text()
		}
	})
	if (selected === 0) return
	$('#preview-list').append(new_row)

	addedgroup = $("#group").text()
	logtext = '<br>You added ' + addedgroup + ' to ' + message
	addLog(logtext)

	$('#groups').empty()
	$('#group').empty()
	$('#group-handin').empty()
}

function delete_row(row) {
	var id = '#' + row
	b=$(id).closest('tr').find('td.os').text()
	$(id).closest('tr').remove()
	st='<br>' + 'You deleted ' + b
    addLog(st);
}

function addLog(logentry) {
	x = document.getElementById("rolling-log")
	x.innerHTML = x.innerHTML + logentry
}

$('#compile').submit(function (e) {
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
			param.push(obj)
			cnt++
		}
	})
	if (cnt === 0) return
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

function setCurrentJob(job_id){
	// event_id = setInterval(trace_job, interval);
	$('#ongoing-task').text(job_id)
	finished_status = false
}


// invoked when job tracking request has been called
function trace_job() {
	var job_id = $('#ongoing-task').text().trim()
    var finished,total;
	console.log("job: "+job_id)
	if(job_id === "" || job_id === 'None' || finished_status) {
		return
	}
    $.ajax({
        url: "/trace_task",
        dataType : "json",
        data: {
        	task_id: job_id,
        },
        success:  function(response) {
        	console.log(response)
            finished = response.finished
            total = response.total
            if(finished === total) {
            	finished_status = true
                // clearInterval(event_id)
            }
        	percent = finished*100/total
        	report = "<span id='task_finished'>"+ finished.toString()+"</span> / "+"<span id='task_total'>"+total.toString()+"</span>"+" compilation finished for job id: "+response.task_id
        	$('#result-trace').css('display','block')
        	$('#result-report').empty()
            $('#result-report').append(report)
        	$('#bar-growth').width(percent.toString()+'%')
        	// adjost log output
        	$('#log-report').empty()
        	for(var i in response.log_report) {
        		// var d = new Date();
        		var log = response.log_report[i]
        		var out_theme = ""
        		var err_theme = ""
        		// console.log(d.year)
        		if(log.err !== "-") {
        			out_theme = "text-align:left;"
        		}
        		if(log.err !== "-") {
        			err_theme = "text-align:left;"
        		}
        		var log_row = "<tr>"+
                    "<td class='report-row' style='column-width: auto;'>"+log.exename.trim()+"</td>"+
                    "<td class='report-row' style='column-width: auto;"+out_theme+"'>"+log.out+"</td>"+
                    "<td class='report-row' style='column-width: auto;"+err_theme+"'>"+log.err+"</td>"+
					// "<td>" + d.year + d.month + d.day + d.hours + d.minutes + d.seconds + "</td>"
                    "</tr>"
                $("#log-report").append(log_row)
        	}
        	$('#trace-wrapper').css("display","block");
        }
    });
    return
}

function getOS() {
	var json_profiles = $('#json_profiles').text()
	if (json_profiles === "" || json_profiles === null) return
	text = JSON.parse(json_profiles)
	var os_list = []
	for (os in text) {
		os_list.push(os)
	}
	os_list.sort()
	var options = ""
	for (os in os_list) {
		options += "<option>" + os_list[os] + "</option>"
	}
	$('#target_os').append(options)

}

function getCompiler(os) {
	$('#compiler').empty()
	$('#os_selected').text(os)
	var compiler_list = []
	for (compiler in text[os]) {
		compiler_list.push(compiler)
	}
	compiler_list.sort()
	var options = "<option value='' disabled selected>Select</option>"
	for (compiler in compiler_list) {
		options += "<option>" + compiler_list[compiler] + "</option>"
	}
	$('#compiler').append(options)
}

function getProfiles(compiler) {
	$('#profiles').empty()
	$('#compiler_selected').text(compiler)
	var os = $('#os_selected').text()
	var plist = text[os][compiler].sort()
	var options = ""
	var boxes = ""
	for (p in plist) {
		options += "<input type='checkbox' onchange='peek(this.id);' name='profile' id='" + plist[p] +
					"' value='" + plist[p] + "'/>" + plist[p] + "<br/>"
		boxes += "<div id='" + plist[p] + "_box'></div>"
	}
	$('#profile_content').append(boxes)
	$('#profiles').append(options)
}

function peek(profile) {
	if (document.getElementById(profile).checked === true) {
		$.ajax({
			type: 'POST',
			url: "/peek_profile",
			dataType: "json",
			data: {
				target_os: $('#os_selected').text(),
				compiler: $('#compiler_selected').text(),
				name: profile,
			},
			success: function (response) {
				if ('message' in response) {
					message += response['message']
					alert(message)
				} else {
					var id = '#' + profile + '_box'
					var message = ""
					message += "<div class='peek_text'> name: &nbsp &nbsp &nbsp &nbsp" + response['name'] + "<br>"
					message += "target_os: &nbsp" + response['target_os'] + "<br>"
					message += "compiler: &nbsp &nbsp" + response['compiler'] + "<br>"
					message += "version: &nbsp &nbsp &nbsp" + response['version'] +  "<br>"
					message += "flag: &nbsp &nbsp &nbsp" + response['flag'] + "<br>"
					message += "uploader: &nbsp &nbsp" + response['uploader'] + "<br>"
					message += "upload_time: &nbsp" + response['upload_time'] + "<br><br></div>"
					$(id).append(message)
				}
			}
		});
	} else {
		var id = '#' + profile + '_box'
		$(id).empty()
	}
}

function display_flags() {
	var json_profiles = $('#json_profiles').text()
	if (json_profiles === "" || json_profiles === null) return
	var plist = JSON.parse(json_profiles)
	var message = ''
	for (p in plist) {
		message += '<div class="js-debug">'
		message += '<button class="button-check-box" id=flag' + p + ' onclick="addflag(this.id)"></button> ' + plist[p] + '</div>'
	}
	$('#display_flags').append(message)
}

function onload_wrapper() {
	getOS()
	display_flags()
	trace_job()
}

window.onload = onload_wrapper;
var event_id = window.setInterval(trace_job, interval);










//**************** function for tar downloading
function download_tar(){
	var id = $('#ongoing-task').text().trim()
	var finished = $('#task_finished').text().trim()
	var total = $('#task_total').text().trim()
	if(finished !== total) return;
	console.log("eligible for download")
	$('input[name="downloadtaskid"]').val(id)
	console.log($('input[name="downloadtaskid"]').val())
	$('#download_full').submit()
}

