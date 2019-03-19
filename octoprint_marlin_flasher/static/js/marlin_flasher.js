$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.sketchName = ko.observable();
        $("#sketch_file").fileupload({
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                new PNotify({
                    title: "Sketch upload successful",
                    text: data.result.ino,
                    type: "success"
                });
                self.sketchName(data.result.ino)
            },
            error: function(jqXHR, status, error) {
                new PNotify({
                    title: "Sketch upload failed",
                    text: "Was it a zip file containing a valid sketch. If so check plugin settings",
                    type: "error",
                    hide: false
                });
            }
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
