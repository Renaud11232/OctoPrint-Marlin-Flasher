$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MarlinFlasherViewModel,
        dependencies: [
            "settingsViewModel"
        ],
        elements: [
            "#settings_plugin_marlin_flasher",
            "#wizard_plugin_marlin_flasher"
        ]
    });
});
