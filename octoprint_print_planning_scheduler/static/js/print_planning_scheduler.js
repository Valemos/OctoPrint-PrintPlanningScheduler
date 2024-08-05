/*
 * View model for OctoPrint-PrintPlanningScheduler
 *
 * Author: Anton Skrypnyk
 * License: AGPLv3
 */
class print_planning_schedulerViewModel
{
    constructor(parameters)
    {
        this.calendar = null;
        this.suggestedJobs = new Array();
        this.plannedJobs = new Array();
        this.COLOR_DISABLED_PRINTING = "#c92662";
        this.COLOR_ENABLED_PRINTING = "#03fc73";
        this.PLUGIN_BASE_URL = "/plugin/print_planning_scheduler";
    }

    onStartupComplete()
    {
        this.initCalendar();
        this.initCalendarControlForms();
        this.updateAllPrintJobs();
    }

    initCalendar()
    {
        $(document).ready(() => {
            const calendarEl = $("#scheduling_calendar").get(0);
            this.calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: "timeGridWeek",
                initialDate: new Date().toISOString().split("T", 1)[1],
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'timeGridWeek,timeGridDay'
                },
                nowIndicator: true,
                navLinks: true,
                selectable: true,
                selectMirror: true,
                select: this.addEventByPrompt.bind(this),
                eventClick: this.onClickEvent.bind(this),
                editable: true,
                dayMaxEvents: true,
                eventSources: [
                    {
                        events: this.getCalendarDisabledIntervals.bind(this),
                        color: this.COLOR_DISABLED_PRINTING,
                        textColor: 'black'
                    },
                    {
                        events: this.getCalendarExcludedIntervals.bind(this),
                        color: this.COLOR_ENABLED_PRINTING,
                        textColor: 'white'
                    }
                ],
            });
            this.calendar.render();

            // Hack around issue https://github.com/fullcalendar/fullcalendar/issues/4976
            window.setTimeout(() => {
                window.dispatchEvent(new Event("resize"));
            }, 100);
        });
    }

    updateAllPrintJobs()
    {
        this.updatePlannedJobs();
        this.updateSuggestedJobs();
    }
    
    updateSuggestedJobs()
    {
        var self = this;
        this.suggestedJobs = new Array();
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/suggested_print_jobs',
            type: 'GET',
            success: function (response) {
                response.jobs.forEach((job) => {
                    self.suggestedJobs.push({
                        id: job._id,
                        name: job.name,
                        description: job.description,
                        duration: job.duration,
                    })
                });
                self.renderSuggestedJobList();
            },
            error: function (xhr, status, error) {
                console.error('Error fetching disabled events:', error);
            }
        });
        
    }

    updatePlannedJobs()
    {
        var self = this;
        this.plannedJobs = new Array();
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/print_job',
            type: 'GET',
            success: function (response) {
                response.jobs.forEach((job) => {
                    self.plannedJobs.push({
                        id: job._id,
                        name: job.name,
                        description: job.description,
                        duration: job.duration,
                    })
                });
                self.renderPlannedJobList();
            },
            error: function (xhr, status, error) {
                console.error('Error fetching disabled events:', error);
            }
        });
    }

    initCalendarControlForms()
    {
        $('#print_job_form').on('submit', e => this.onAddPrintJobSubmit(e));
        $('#schedule_upload_form').on('submit', e => this.onScheduleFileUploadSubmit(e));
        $('#scheduling_calendar_event_form').on('submit', e => this.onAddCalendarEventSubmit(e));
    }

    getCalendarDisabledIntervals(info, successCallback, failureCallback)
    {
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/disabled_event',
            type: 'GET',
            data: {
                start: info.start.toISOString(),
                end: info.end.toISOString(),
            },
            success: function(response) {
                successCallback(
                    response.slice().map((event) => {
                            return {
                                title: event.name,
                                start: new Date(event.start).toISOString(),
                                end: new Date(event.end).toISOString(),
                            }
                        }));
            },
            error: function(xhr, status, error) {
                failureCallback(error);
            }
        });
    }

    getCalendarExcludedIntervals(info, successCallback, failureCallback)
    {
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/excluded_interval',
            type: 'GET',
            data: {
                start: info.start.toISOString(),
                end: info.end.toISOString(),
            },
            success: function(response) {
                successCallback(
                    response.slice().map((event) => {
                            return {
                                title: event.name,
                                start: new Date(event.start).toISOString(),
                                end: new Date(event.end).toISOString(),
                            }
                        }));
            },
            error: function(xhr, status, error) {
                failureCallback(error);
            }
        });
    }

    addEventByPrompt(newEventProps)
    {
        var title = prompt('Event Title:');
        if (title) {
            this.calendar.addEvent({
                title: title,
                start: newEventProps.start,
                end: newEventProps.end,
                allDay: newEventProps.allDay
            });
        }
        this.calendar.unselect();
    }

    onClickEvent(eventClick)
    {
        if (confirm('Are you sure you want to delete this event?')) {
            eventClick.event.remove()
        }
    }

    onScheduleFileUploadSubmit(event) {
        event.preventDefault();
        const fileEl = $(event.target).find('[name="file"]').get(0);
        var file = fileEl.files[0];
        var reader = new FileReader();
        var self = this;
        reader.onload = (event) => {
            const fileContent = event.target.result;
            $.ajax({
                url: self.PLUGIN_BASE_URL + '/upload_schedule',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ content: fileContent }),
                success: (response) => {
                    $('#message').text(response.message).css('color', 'green');
                    self.calendar.refetchEvents();
                },
                error: (xhr, status, error) => {
                    var errorMessage = xhr.responseJSON ? xhr.responseJSON.message : 'An error occurred';
                    $('#message').text(errorMessage).css('color', 'red');
                }
            });
        };
        reader.readAsText(file);
    }

    onAddCalendarEventSubmit(event)
    {
        event.preventDefault();
        const formData = new FormData($(event.target).get(0));

        var newEvent = {
            title: formData.title,
            start: new Date(formData.start).toISOString(),
            end: new Date(formData.end).toISOString()
        };

        if (newEvent.start == "")
        {
            newEvent.start = new Date(Date.now()).toISOString();
        }
        if (newEvent.end == "")
        {
            var newEnd = new Date(newEvent.start);
            newEnd.setMinutes(newEnd.getMinutes() + 30);
            newEvent.end = newEnd.toISOString();
        }
        
        var isPrintingEnabled = form.find('[name="isPrintingEnabled"]').val();
        newEvent.eventColor = isPrintingEnabled ? COLOR_ENABLED_PRINTING : COLOR_DISABLED_PRINTING;

        if (isPrintingEnabled)
        {
            this.sendDisabledEvent({
                name: newEvent.title,
                start: newEvent.start,
                end: newEvent.end,
            },
            () => this.calendar.addEvent(newEvent));
        } else {
            this.sendExcludedInterval({
                start: newEvent.start,
                end: newEvent.end,
            },
            () => this.calendar.addEvent(newEvent));
        }
    }

    onAddPrintJobSubmit(submitEvent)
    {
        submitEvent.preventDefault();
        const formData = new FormData($(submitEvent.target).get(0));
        var printJob = Object.fromEntries(formData);
        console.log('Print Job:', printJob);
        
        var self = this;
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/print_job',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(printJob),
            success: function (response) {
                console.log('Print job submit success:', response);
                printJob.id = response._id;
                self.suggestedJobs.push(printJob);
                self.renderJobLists();
            },
            error: function (xhr, status, error) {
                console.error('Error submitting job:', error);
            }
        });
    }

    _formatDuration(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);

        const paddedHrs = String(hrs).padStart(2, '0');
        const paddedMins = String(mins).padStart(2, '0');

        return `${paddedHrs}:${paddedMins}`;
    }

    _createPrintJobElement(job)
    {
        const durationStr = this._formatDuration(job.duration);
        const finishTime = new Date(Date.now() + job.duration).toLocaleString();
        return $(`
            <div class="job-item" data-id="${job._id}">
                <h3 class="job-name">${job.name}</h3>
                <p class="job-duration">Duration: ${durationStr}</p>
                <p class="job-finish-time">Finishes at: ${finishTime}</p>
            </div>
        `)
    }

    renderJobLists() {
        this.renderSuggestedJobList();
        this.renderPlannedJobList();
    }

    renderSuggestedJobList()
    {
        var suggestedJobList = $('#suggested_print_job_list');
        suggestedJobList.innerHTML = '';
        if (this.suggestedJobs.length == 0)
        {
            suggestedJobList.append(
                this.plannedJobs.length > 0 ?
                    "<p>Cannot suggest any print job</p>" :
                    "<p>No planned jobs</p>");
        } else {
            this.suggestedJobs.forEach(job => {
                const jobItem = this._createPrintJobElement(job);
                jobItem.click(() => this.openJobDialog(job._id));
                suggestedJobList.append(jobItem);
            });
        }
    }

    renderPlannedJobList() {
        var plannedJobList = $('#planned_print_job_list');
        plannedJobList.innerHTML = '';
        if (this.plannedJobs.length == 0)
        {
            plannedJobList.append("<p>No planned jobs</p>");
        } else {
            this.plannedJobs.forEach(job => {
                const jobItem = this._createPrintJobElement(job);
                jobItem.click(() => this.openJobDialog(job._id));
                plannedJobList.append(jobItem);
            });
        }
    }

    openJobDialog(id) {
        const job = this.plannedJobs.find(job => job._id === id);
        if (job) {
            // Create the dialog content dynamically
            const dialogContent = `
                <form id="start_job_dialog" data-id="${job.id}">
                    <h3>${job.name}</h3>
                    <p>Duration: ${job.duration}</p>
                    <p>${job.description}</p>
                    <input type="submit" value="Submit">
                    <input type="reset" value="Cancel">
                </form>
            `;

            $('#start_job_dialog').remove();
            $('#start_job_overlay').remove();

            $('body').append(dialogContent);
            $('body').append('<div id="start_job_overlay"></div>');
            $('#start_job_dialog').on('submit', (e) => this.submitStartJob(e))
            $('#start_job_dialog').on('reset', (e) => this.closeJobDialog())
            $('#start_job_overlay').on('click', (e) => this.closeJobDialog())

            $('#start_job_overlay').show();
            $('#start_job_dialog').show();
        }
    }

    closeJobDialog() {
        $('#start_job_overlay').hide();
        $('#start_job_dialog').hide();
        $('#start_job_overlay').remove();
        $('#start_job_dialog').remove();
    }
    
    submitStartJob(submitEvent) {
        const id = $(submitEvent.target).data('id');
        const job = jobs.find(job => job.id === id);
        var self = this;
        if (job) {
            startPrintJob(job).then(() => {
                jobs = jobs.filter(job => job.id !== id);
                self.updateAllPrintJobs();
                self.closeJobDialog();
            }).catch(error => {
                console.error('Failed to start print job:', error);
            });
        }
    }

    updateJobList(newJobs) {
        jobs = newJobs;
        renderJobList();
    }

    startPrintJob(job) {
        return new Promise((resolve, reject) => {
            setTimeout(() => resolve(), 1000);  // Simulate async operation
        });
    }
    sendDisabledEvent(newEvent) {
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/disabled_event',
            type: 'POST',
            data: newEvent,
            success: function (response) {
                console.log('Disabled event post:', response);
            },
            error: function (xhr, status, error) {
                console.error('Error fetching disabled events:', error);
            }
        });
    }

    sendExcludedInterval(excludedInterval, success=null)
    {
        $.ajax({
            url: this.PLUGIN_BASE_URL + '/excluded_interval',
            type: 'POST',
            data: excludedInterval,
            success: success != null ? success : function(response) {
                console.log('Interval excluded successfully:', response);
            },
            error: function(xhr, status, error) {
                console.error('Error excluding interval:', error);
            }
        });
    }
}


$(function() {
    OCTOPRINT_VIEWMODELS.push({
        construct: print_planning_schedulerViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        elements: [ "#tab_plugin_print_planning_scheduler" ]
    });
});
