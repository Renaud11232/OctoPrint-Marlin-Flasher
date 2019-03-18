$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.sketchFile = $("#sketch_file");
        self.sketchFile .fileupload({
            dataType: "json",
            maxNumberOfFiles: 1,
            autoUpload: true,
            headers: OctoPrint.getRequestHeaders()
        });
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MarlinFlasherViewModel,
        dependencies: [
            "settingsViewModel"
        ],
        elements: [
            "#settings_plugin_marlin_flasher",
            "#wizard_plugin_marlin_flasher",
            "#tab_plugin_marlin_flasher"
        ]
    });
});
