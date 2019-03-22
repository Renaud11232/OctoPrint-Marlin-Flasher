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
                },
                {
                    field: "dl_btn",
                    title: '<i class="icon-download-alt"></i>',
                    width: "54px",
                    halign: "center"
                },
                {
                    field: "rm_btn",
                    title: '<i class="icon-trash"></i>',
                    width: "54px",
                    halign: "center"
                }
            ]
        });
        $("#cores-search-form").submit(function(event) {
            $("#cores-table").bootstrapTable("showLoading");
            $.getJSON("/plugin/marlin_flasher/cores", {
                query: $("#cores-search-text").val()
            }).done(function (data) {
                var tableData = data.Platforms;
                tableData.forEach(function(element) {
                    element.dl_btn = '<button class="btn btn-primary" type="button" value="' + element.ID + '@' + element.Version + '"><i class="icon-download-alt"></i></button>'
                    element.rm_btn = '<button class="btn btn-danger" type="button" value="' + element.ID + '"><i class="icon-trash"></i></button>'
                });
                $("#cores-table").bootstrapTable("load", tableData);
            }).fail(function() {
                new PNotify({
                    title: "Core search failed",
                    text: "Is the plugin properly configured ?",
                    type: "error",
                    hide: false
                });
            }).always(function() {
                $("#cores-table").bootstrapTable("hideLoading");
            });
            event.preventDefault();
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
