// static/js/scripts.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to get a cookie by name
    function getCookie(name) {
        let dc = document.cookie;
        let prefix = name + "=";
        let begin = dc.indexOf("; " + prefix);
        if (begin == -1) {
            begin = dc.indexOf(prefix);
            if (begin != 0) return null;
        }
        else {
            begin += 2;
        }
        let end = document.cookie.indexOf(";", begin);
        if (end == -1) {
            end = dc.length;
        }
        return decodeURI(dc.substring(begin + prefix.length, end));
    }

    // Function to delete a cookie by name
    function deleteCookie(name) {
        document.cookie = name+'=; Max-Age=-99999999; path=/';
    }

    // Check for existing task on page load
    var existing_task = getCookie('current_task');
    if(existing_task){
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-bar').innerText = '0%';
        document.getElementById('status-text').innerText = 'Resuming previous task...';
        document.getElementById('stop-button').style.display = 'block';
        pollProgress(existing_task);
    } else {
        document.getElementById('stop-button').style.display = 'none';
    }

    document.getElementById('upload-form').addEventListener('submit', function(event){
        event.preventDefault();
        var formData = new FormData(this);
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-bar').innerText = '0%';
        document.getElementById('status-text').innerText = 'Uploading video...';
        document.getElementById('stop-button').style.display = 'block';
        document.getElementById('gif-previews').innerHTML = '';

        fetch("/upload", {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(response => {
            if(response.task_id){
                var task_id = response.task_id;
                console.log(`Task ${task_id} initiated.`);
                pollProgress(task_id);
            }
            else if(response.error){
                console.error('Upload Error:', response.error);
                alert(response.error);
                document.getElementById('progress-container').style.display = 'none';
                document.getElementById('stop-button').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Upload Fetch Error:', error);
            alert('An error occurred during upload.');
            document.getElementById('progress-container').style.display = 'none';
            document.getElementById('stop-button').style.display = 'none';
        });
    });

    document.getElementById('stop-button').addEventListener('click', function(){
        var task_id = getCookie('current_task');
        if(task_id){
            console.log(`Stop requested for task ${task_id}.`);
            fetch("/stop/" + task_id, {
                method: 'POST',
            })
            .then(response => response.json())
            .then(response => {
                if(response.message){
                    alert(response.message);
                    console.log(`Task ${task_id}: ${response.message}`);
                }
                pollProgress(task_id); // Update the progress/status
            })
            .catch(error => {
                console.error('Stop Task Fetch Error:', error);
                alert('An error occurred while stopping the task.');
            });
        }
    });

    function pollProgress(task_id){
        var interval = setInterval(function(){
            fetch("/progress/" + task_id)
            .then(response => response.json())
            .then(response => {
                if(response.progress !== undefined){
                    document.getElementById('progress-bar').style.width = response.progress + '%';
                    document.getElementById('progress-bar').innerText = response.progress + '%';
                    console.log(`Task ${task_id}: Progress - ${response.progress}%`);
                }
                if(response.status){
                    document.getElementById('status-text').innerText = response.status;
                    console.log(`Task ${task_id}: Status - ${response.status}`);
                }
                if(response.status === 'Completed'){
                    clearInterval(interval);
                    document.getElementById('progress-bar').style.width = '100%';
                    document.getElementById('progress-bar').innerText = '100%';
                    document.getElementById('status-text').innerText = '🎉 GIF Generation Completed! 🎉';
                    document.getElementById('stop-button').style.display = 'none';
                    displayGIFs(response.gifs);
                    deleteCookie('current_task');
                    console.log(`Task ${task_id}: Completed successfully.`);
                }
                else if(response.status.startsWith('Failed') || response.status === 'Stopped by User'){
                    clearInterval(interval);
                    alert(response.status);
                    console.log(`Task ${task_id}: ${response.status}`);
                    document.getElementById('progress-container').style.display = 'none';
                    document.getElementById('stop-button').style.display = 'none';
                    deleteCookie('current_task');
                }
            })
            .catch(error => {
                console.error('Poll Progress Fetch Error:', error);
                clearInterval(interval);
                alert('Failed to retrieve progress.');
                document.getElementById('progress-container').style.display = 'none';
                document.getElementById('stop-button').style.display = 'none';
                deleteCookie('current_task');
            });
        }, 500); // Poll every 0.5 seconds for more frequent updates
    }

    function displayGIFs(gifs){
        if(gifs.length > 0){
            var html = '<h2 class="mb-3 text-center">✨ Generated GIFs ✨</h2><div class="row justify-content-center">';
            gifs.forEach(function(gif){
                var gif_url = "/static/uploads/output/" + gif;
                html += `
                <div class="col-md-4 text-center mb-4">
                    <div class="card h-100">
                        <img src="${gif_url}" class="card-img-top img-fluid" alt="GIF Preview">
                        <div class="card-body d-flex flex-column">
                            <a href="/download/${gif}" class="btn btn-success mt-auto">Download</a>
                        </div>
                    </div>
                </div>
                `;
            });
            html += '</div>';
            document.getElementById('gif-previews').innerHTML = html;
            console.log('GIFs displayed:', gifs);
        }
        document.getElementById('progress-container').style.display = 'none';
    }
});
