function editProfile(os, compiler, version, name) {
    document.getElementById('update_profile').style.visibility = 'visible'
    $.ajax({
        type: 'POST',
        url: "/getProfile",
        dataType: "json",
        data: {
            target_os: os,
            compiler: compiler,
            version: version,
            name: name,
        },
        success: function (response) {
            document.getElementById('old_target_os').value = response['target_os']
            document.getElementById('old_compiler').value = response['compiler']
            document.getElementById('old_version').value = response['version']
            document.getElementById('old_name').value = response['name']

            $('#target_os').empty()
            $('#target_os').append(response['target_os'])
            $('#compiler').empty()
            $('#compiler').append(response['compiler'])
            $('#version').empty()
            $('#version').append(response['version'])
            $('#name').empty()
            $('#name').append(response['name'])
            $('#flag').empty()
            var plist = JSON.parse(response['flag'])
            for (p in plist) {
                $('#flag').append(plist[p])
                if (p != plist.length - 1) {
                    $('#flag').append('\n')
                }
            }
            $('#uploader').empty()
            $('#uploader').append(response['uploader'])
            $('#upload_time').empty()
            $('#upload_time').append(response['upload_time'])
        }
    });
}

function editCompiler(os, compiler, version) {
    document.getElementById('update_compiler').style.visibility = 'visible'
    $.ajax({
        type: 'POST',
        url: "/getCompiler",
        dataType: "json",
        data: {
            target_os: os,
            compiler: compiler,
            version: version,
        },
        success: function (response) {
            document.getElementById('old_target_os').value = response['target_os']
            document.getElementById('old_compiler').value = response['compiler']
            document.getElementById('old_version').value = response['version']

            $('#target_os').empty()
            $('#target_os').append(response['target_os'])
            $('#compiler').empty()
            $('#compiler').append(response['compiler'])
            $('#version').empty()
            $('#version').append(response['version'])
            $('#ip').empty()
            $('#ip').append(response['ip'])
            $('#port').empty()
            $('#port').append(response['port'])
            $('#http_path').empty()
            $('#http_path').append(response['http_path'])
            $('#invoke_format').empty()
            $('#invoke_format').append(response['invoke_format'])
        }
    });
}