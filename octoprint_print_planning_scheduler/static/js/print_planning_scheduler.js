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
        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    onStartupComplete()
    {
        this.initCalendar();
        this.initNewEventForm();
    }

    initCalendar()
    {
        var calendarEl = document.getElementById('scheduling_calendar');
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
        });

        this.calendar.changeView("timeGridWeek");
        this.calendar.render();
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

    initNewEventForm()
    {
        const form = $('#scheduling_calendar_event_form');
        $('#scheduling_calendar_event_submit').on('click', this.addFormEvent.bind(this, form));
    }

    addFormEvent(form)
    {
        var newEvent = {
            title: form.find('[name="title"]').val(),
            url: form.find('[name="url"]').val(),
            start: form.find('[name="start"]').val(),
            end: form.find('[name="end"]').val()
        };

        if (newEvent.start == "")
        {
            newEvent.start = new Date().toISOString();
        }
        if (newEvent.end == "")
        {
            var newEnd = new Date(newEvent.start);
            newEnd.setMinutes(newEnd.getMinutes() + 30);
            newEvent.end = newEnd.toISOString();
        }

        this.addCalendarEvent(newEvent);
    }

    addCalendarEvent(event) {
        if (this.calendar == null)
        {
            console.log("Cannot add event for non existing calendar")
            return
        }
        this.calendar.addEvent(event);
        console.info(event);
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
