$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;

    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MarlinFlasherViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_marlin_flasher, #tab_plugin_marlin_flasher, ...
        elements: [ /* ... */ ]
    });
});
