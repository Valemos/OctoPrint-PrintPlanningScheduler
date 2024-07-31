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
        this.COLOR_DISABLED_PRINTING = "#c92662";
        this.COLOR_ENABLED_PRINTING = "#03fc73";
        this.PLUGIN_BASE_URL = "/plugin/print_planning_scheduler";
    }

    onStartupComplete()
    {
        this.initCalendar();
        this.initCalendarControlForms();
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
                        color: self.COLOR_DISABLED_PRINTING,
                        textColor: 'black'
                    },
                    {
                        events: this.getCalendarExcludedIntervals.bind(this),
                        color: self.COLOR_ENABLED_PRINTING,
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

    initCalendarControlForms()
    {
        $('#schedule_upload_form').on('submit', e => this.onScheduleFileUploadSubmit(e));
        $('#scheduling_calendar_event_form').on('submit', e => this.onAddCalendarEventSubmit(e));
        $('#print_job_form').on('submit', e => this.onAddPrintJobSubmit(e));
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
                    self.calendar.render();
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

    onAddPrintJobSubmit(event)
    {
        submit_event.preventDefault();
        const formData = new FormData($(event.target).get(0));

        const printJob = {
            name: formData.title,
            duration: formData.duration,
            description: formData.description
        };

        console.log('Print Job:', printJob);
        // TODO: send job
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
