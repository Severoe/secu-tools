var interval = 1000;

//send request to check job process
function tracejob() {
	var job_id = $('#task_id').text()
    var finished,total;
	// console.log("job: "+job_id)
	if(job_id === "" ) {
		return
	}
    $.ajax({
        url: "/trace",
        dataType : "json",
        data: {
        	task_id: job_id,
        },
        success:  function(response) {
        	console.log(response)
            finished = response.finished
            total = response.total
        	percent = finished*100/total
        	report = finished.toString()+" / "+total.toString()+" compilation finished for job id: "+response.task_id
        	$('#result-trace').css('display','block')
            $('#result-report').text(report)
        	$('#bar-growth').width(percent.toString()+'%')
        }
    });
    if(finished === total) {
        clearInterval(event_id)
    }
    return
}



window.onload = tracejob;
var event_id = window.setInterval(tracejob, interval);