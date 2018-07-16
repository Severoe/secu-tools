var text = ""

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
            
            getOS(response['target_os'])
            getCompiler(response['target_os'], response['compiler'])
            getVersion(response['compiler'], response['version'])
            
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
            document.getElementById('upload_time').value = response['upload_time']
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

            getOS(response['target_os'])
            getCompiler(response['target_os'], response['compiler'])
            getVersion(response['compiler'], response['version'])

            $('#ip').empty()
            $('#ip').append(response['ip'])
            $('#port').empty()
            $('#port').append(response['port'])
            $('#flag').empty()
            var plist = JSON.parse(response['flag']).sort()
            for (p in plist) {
                $('#flag').append(plist[p])
                if (p != plist.length - 1) {
                    $('#flag').append('\n')
                }
            }
            $('#http_path').empty()
            $('#http_path').append(response['http_path'])
            $('#invoke_format').empty()
            $('#invoke_format').append(response['invoke_format'])
        }
    });
}

function main_page() {
    window.location.href = '/';
}

function read_profiles() {
    var json_profiles = $('#json_profiles').text()
    if (json_profiles === "" || json_profiles === null) return
    text = JSON.parse(json_profiles)
}

function getOS(target_os) {
    $('#target_os').empty()
    var os_list = []
    for (os in text) {
        os_list.push(os)
    }
    os_list.sort()
    var options = ""
    for (os in os_list) {
        if (os_list[os] === target_os)
            options += "<option selected>" + os_list[os] + "</option>"
        else
            options += "<option>" + os_list[os] + "</option>"
    }
    $('#target_os').append(options)
}

function getCompiler(os, target_compiler) {
    $('#compiler').empty()
    $('#os_selected').text(os)

    var compiler_list = []
    for (compiler in text[os]) {
        compiler_list.push(compiler)
    }
    compiler_list.sort()
    var options = ""
    if (target_compiler === "") {
        $('#version').empty()
        options += "<option value='' disabled selected>Select</option>"
        for (compiler in compiler_list) {
            options += "<option>" + compiler_list[compiler] + "</option>"
        }
    } else {
        for (compiler in compiler_list) {
            if (compiler_list[compiler] === target_compiler)
                options += "<option selected>" + compiler_list[compiler] + "</option>"
            else
                options += "<option>" + compiler_list[compiler] + "</option>"
        }
    }
    $('#compiler').append(options)
}

function getVersion(compiler, target_version) {
    $('#version').empty()
    var os = $('#os_selected').text()
    var plist = text[os][compiler].sort()
    var options = ""
    if (target_version === "") {
        options += "<option value='' disabled selected>Select</option>"
        for (p in plist) {
            options += "<option>" + plist[p] + "</option>"
        }
    } else {
        for (p in plist) {
            if (plist[p] === target_version) {
                options += "<option selected>" + plist[p] + "</option>"
            }
            else {
                options += "<option>" + plist[p] + "</option>"
            }
        }
    }
    $('#version').append(options)
}

function onload_wrapper() {
    read_profiles()
}

window.onload = onload_wrapper;