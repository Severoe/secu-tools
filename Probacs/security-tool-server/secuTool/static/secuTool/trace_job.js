var interval = 1000;

//send request to check job process
function tracejob() {
	var job_id = $('#task_id').text()
	// console.log("job: "+job_id)
	if(job_id === "" || ) {
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
        	var report = str(response.finished)+" / "+str(response.total)+" compilation finished for job id: "+response.task_id
        	$('#result-trace').text(report)
        }
    });
    return
}



window.onload = tracejob;
window.setInterval(tracejob, interval);