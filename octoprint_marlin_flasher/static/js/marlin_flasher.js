$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        $("#sketch_file").fileupload({
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                new PNotify({
                    title: "Sketch upload successful",
                    text: data.result.ino,
                    type: "success"
                });
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
        $("#cores-table").bootstrapTable({
            columns: [
                {
                    field: "ID",
                    title: "ID"
                },
                {
                    field: "Version",
                    title: "Version"
                },
                {
                    field: "Name",
                    title: "Name"
                }
            ]
        });
        $("#test-button").click(function() {
            $("#cores-table").bootstrapTable("load", [
                {
                    ID: "test-id",
                    Version: "1.2.5",
                    Name: "Test Name"
                }
            ]);
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
