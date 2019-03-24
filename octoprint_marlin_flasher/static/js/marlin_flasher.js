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
                    text: jqXHR.responseJSON.error,
                    type: "error"
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
                    title: $("<i>", {
                        class: "icon-download-alt"
                    }).prop("outerHTML"),
                    width: "54px",
                    halign: "center"
                },
                {
                    field: "rm_btn",
                    title: $("<i>", {
                        class: "icon-trash"
                    }).prop("outerHTML"),
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
                if(data.hasOwnProperty("Platforms")) {
                    var tableData = data.Platforms;
                    tableData.forEach(function(element) {
                        element.dl_btn = $("<button>", {
                            class: "btn btn-primary core-install-btn",
                            type: "button",
                            value: element.ID + "@" + element.Version,
                            html: $("<i>", {
                                class: "icon-download-alt"
                            }).prop("outerHTML")
                        }).prop("outerHTML");
                        element.rm_btn = $("<button>", {
                            class: "btn btn-danger core-uninstall-btn",
                            type: "button",
                            value: element.ID,
                            html: $("<i>", {
                                class: "icon-trash"
                            }).prop("outerHTML")
                        }).prop("outerHTML");
                    });
                    $("#cores-table").bootstrapTable("load", tableData);
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Core search failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
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
                self.loadBoardSelectOptions();
                new PNotify({
                    title: "Core install successful",
                    text: "Successfully installed " + data.core,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Core install failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
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
                self.loadBoardSelectOptions();
                new PNotify({
                    title: "Core uninstall successful",
                    text: "Successfully uninstalled " + data.core,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Core uninstall failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $("#cores-table").bootstrapTable("hideLoading");
            });
        });
        $("#libs-table").bootstrapTable({
            columns: [
                {
                    field: "Name",
                    title: "Name"
                },
                {
                    field: "dl_btn",
                    title: $("<i>", {
                        class: "icon-download-alt"
                    }).prop("outerHTML"),
                    width: "54px",
                    halign: "center"
                },
                {
                    field: "rm_btn",
                    title: $("<i>", {
                        class: "icon-trash"
                    }).prop("outerHTML"),
                    width: "54px",
                    halign: "center"
                }
            ]
        });
        $("#libs-search-form").submit(function(event) {
            $("#libs-table").bootstrapTable("showLoading");
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/libs/search",
                data: {
                    query: $("#libs-search-text").val()
                }
            }).done(function (data) {
                if(data.hasOwnProperty("libraries")) {
                    var tableData = data.libraries;
                    tableData.forEach(function(element) {
                        element.dl_btn = $("<button>", {
                            class: "btn btn-primary lib-install-btn",
                            type: "button",
                            value: element.Name,
                            html: $("<i>", {
                                class: "icon-download-alt"
                            }).prop("outerHTML")
                        }).prop("outerHTML");
                        element.rm_btn = $("<button>", {
                            class: "btn btn-danger lib-uninstall-btn",
                            type: "button",
                            value: element.Name,
                            html: $("<i>", {
                                class: "icon-trash"
                            }).prop("outerHTML")
                        }).prop("outerHTML");
                    });
                    $("#libs-table").bootstrapTable("load", tableData);
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Lib search failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $("#libs-table").bootstrapTable("hideLoading");
            });
            event.preventDefault();
        });
        $(document).on("click", "button.lib-install-btn", function() {
            $("#libs-table").bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/libs/install",
                data: {
                    lib: $(this).val()
                }
            }).done(function(data) {
                new PNotify({
                    title: "Lib install successful",
                    text: "Successfully installed " + data.lib,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Lib install failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $("#libs-table").bootstrapTable("hideLoading");
            });
        });
        $(document).on("click", "button.lib-uninstall-btn", function() {
            $("#libs-table").bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/libs/uninstall",
                data: {
                    lib: $(this).val()
                }
            }).done(function(data) {
                new PNotify({
                    title: "Lib uninstall successful",
                    text: "Successfully uninstalled " + data.lib,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Lib uninstall failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $("#libs-table").bootstrapTable("hideLoading");
            });
        });
        self.loadBoardSelectOptions = function() {
            $("#fqbn").empty();
            $("#fqbn").append($("<option>", {
                disabled: true,
                selected: true,
                value: "",
                text: "Please select one"
            }));
            $("#flash-options").empty();
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/board/listall",
            }).done(function (data) {
                if(data.boards) {
                    data.boards.forEach(function(board) {
                        $("#fqbn").append($("<option>", {
                            text: board.name,
                            value: board.fqbn
                        }));
                    });
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Board list fetch failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            });
        };
        self.loadBoardSelectOptions();
        $("#form-flash").submit(function(event) {
            $("#flash-button").button("loading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/flash",
                data: $("#form-flash").serialize()
            }).done(function (data) {
                new PNotify({
                    title: "Flashing successful",
                    text: data.message,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Flashing failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $("#flash-button").button("reset");
            });
            event.preventDefault();
        });
        $("#fqbn").change(function() {
            $("#flash-options").empty();
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/board/details",
                data: {
                    fqbn: $("#fqbn").val()
                }
            }).done(function (data) {
                if(data) {
                    data.ConfigOptions.forEach(function(o) {
                        var controlGroup = $("<div>", {
                            class: "control-group"
                        });
                        controlGroup.append($("<label>", {
                            class: "control-label",
                            for: "flash-option-" + o.Option,
                            text: o.OptionLabel
                        }));
                        var controls = $("<div>", {
                            class: "controls"
                        });
                        var select = $("<select>", {
                            id: "flash-option-" + o.Option,
                            name: o.Option,
                            required: true
                        });
                        o.Values.forEach(function(v) {
                            var option = $("<option>", {
                                value: v.Value,
                                text: v.ValueLabel
                            });
                            if(v.hasOwnProperty("Selected") && v.Selected) {
                                option.prop("selected", true)
                            }
                            select.append(option);
                        });
                        controls.append(select);
                        controlGroup.append(controls);
                        $("#flash-options").append(controlGroup);
                    });
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: "Board option fetch failed",
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
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
