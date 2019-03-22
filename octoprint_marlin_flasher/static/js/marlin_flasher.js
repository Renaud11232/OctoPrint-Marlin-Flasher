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
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/cores/search",
                data: {
                    query: $("#cores-search-text").val()
                }
            }).done(function (data) {
                var tableData = data.Platforms;
                tableData.forEach(function(element) {
                    element.dl_btn = '<button class="btn btn-primary core-install-btn" type="button" value="' + element.ID + '@' + element.Version + '"><i class="icon-download-alt"></i></button>'
                    element.rm_btn = '<button class="btn btn-danger core-uninstall-btn" type="button" value="' + element.ID + '"><i class="icon-trash"></i></button>'
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
        $(document).on("click", "button.core-install-btn", function() {
            $("#cores-table").bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/cores/install",
                data: {
                    core: $(this).val()
                }
            }).done(function(data) {
                new PNotify({
                    title: "Core install successful",
                    text: "Successfully installed " + data.core,
                    type: "success"
                });
            }).fail(function() {
                new PNotify({
                    title: "Core install failed",
                    text: "Is the plugin properly configured ?",
                    type: "error",
                    hide: false
                });
            }).always(function() {
                $("#cores-table").bootstrapTable("hideLoading");
            });
        });
        $(document).on("click", "button.core-uninstall-btn", function() {
            $("#cores-table").bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/cores/uninstall",
                data: {
                    core: $(this).val()
                }
            }).done(function(data) {
                new PNotify({
                    title: "Core uninstall successful",
                    text: "Successfully uninstalled " + data.core,
                    type: "success"
                });
            }).fail(function() {
                new PNotify({
                    title: "Core uninstall failed",
                    text: "Was it installed ? Is the plugin properly configured ?",
                    type: "error",
                    hide: false
                });
            }).always(function() {
                $("#cores-table").bootstrapTable("hideLoading");
            });
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
